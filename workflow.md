# Inspect Checkpoint Plugin — Workflow

## Component Overview

```mermaid
graph TD
    User["User / Inspect AI eval()"]

    subgraph Plugin["inspect-checkpoint-plugin"]
        Init["create_checkpoint_hook()\n__init__.py"]
        Config["CheckpointConfig\nconfig.py"]
        Hook["CheckpointHook\nhooks.py"]
        Manager["CheckpointManager\ncheckpoint.py"]
        Resume["resume.py\nfind_latest_checkpoint()\nload_latest_checkpoint()"]
        Utils["utils.py\ncheckpoint_name()"]
        Compression["compression.py\ncompress_log_data()"]
        MultiModel["multi_model.py\nmodel_subdir()\nmerge_logs()"]
        Dashboard["dashboard/app.py\nStreamlit UI"]
    end

    Storage[("Storage\nS3 / local\n(fsspec)")]
    InspectAI["inspect_ai\nwrite_eval_log()\nlist_eval_logs()\nread_eval_log()"]

    User -->|"create_checkpoint_hook()"| Init
    Init -->|"creates"| Config
    Init -->|"creates"| Hook
    Hook -->|"owns"| Manager
    Hook -->|"on_task_start"| Resume
    Hook -->|"on_task_end"| Manager
    Manager -->|"checkpoint_name()"| Utils
    Manager -->|"write_eval_log()"| InspectAI
    Resume -->|"list_eval_logs()\nread_eval_log()"| InspectAI
    InspectAI <-->|"read / write\n.json.gz"| Storage
    Dashboard -->|"list_eval_logs()\nread_eval_log()"| InspectAI
    MultiModel -.->|"used by caller\nto build output_dir"| Hook
    Compression -.->|"utility\n(standalone)"| Storage
```

---

## Eval Lifecycle Sequence

```mermaid
sequenceDiagram
    actor User
    participant eval as Inspect eval()
    participant hook as CheckpointHook
    participant mgr  as CheckpointManager
    participant res  as resume.py
    participant ai   as inspect_ai
    participant s3   as Storage (S3/local)

    User->>eval: eval(task, model, hooks=[hook])

    rect rgb(220, 240, 255)
        note over eval,hook: Task Start
        eval->>hook: on_task_start(data)
        alt resume=True and output_dir set
            hook->>res: load_latest_checkpoint(output_dir)
            res->>ai: list_eval_logs(output_dir)
            ai->>s3: list *.json.gz
            s3-->>ai: [EvalLogInfo, ...]
            ai-->>res: sorted by mtime desc
            res->>ai: read_eval_log(latest.name)
            ai->>s3: read file
            s3-->>ai: .json.gz bytes
            ai-->>res: EvalLog
            res-->>hook: prior_log (stored as _prior_log)
        else resume=False or no checkpoints
            hook-->>eval: (no-op)
        end
    end

    loop For each sample
        eval->>eval: run sample
    end

    rect rgb(220, 255, 220)
        note over eval,hook: Task End
        eval->>hook: on_task_end(data)
        hook->>mgr: checkpoint(data.log)
        alt enabled=True
            mgr->>mgr: checkpoint_name() → checkpoint_<ts>.json.gz
            mgr->>ai: write_eval_log(log, location)
            ai->>s3: write .json.gz
            s3-->>ai: ok
            mgr->>mgr: update last_checkpoint_time
        else enabled=False
            mgr-->>hook: (no-op)
        end
    end

    eval-->>User: EvalLog
```

---

## Resume Flow

```mermaid
flowchart TD
    A([Task starts]) --> B{resume=True\nand output_dir set?}
    B -- No --> C([Continue fresh])
    B -- Yes --> D[list_eval_logs\noutput_dir]
    D --> E{Any logs\nfound?}
    E -- No --> C
    E -- Yes --> F[Sort by mtime\ndescending]
    F --> G[read_eval_log\nlatest.name]
    G --> H[Store as\n_prior_log]
    H --> I([Caller may\nrestore state\nfrom _prior_log])
```

---

## Checkpoint Write Flow

```mermaid
flowchart TD
    A([checkpoint called]) --> B{enabled?}
    B -- No --> Z([return — no write])
    B -- Yes --> C["checkpoint_name()\n→ checkpoint_YYYYMMDD_HHMMSS.json"]
    C --> D["append .gz suffix\n→ checkpoint_YYYYMMDD_HHMMSS.json.gz"]
    D --> E["build location\noutput_dir/filename"]
    E --> F["write_eval_log(log, location)\nvia inspect_ai + fsspec"]
    F --> G["update\nlast_checkpoint_time"]
    G --> H([done])
```

---

## Multi-Model Setup

```mermaid
flowchart LR
    Base["s3://bucket/run_123"]
    Base --> GPT["model_subdir(base, 'openai/gpt-5')\n→ s3://bucket/run_123/openai_gpt-5"]
    Base --> Claude["model_subdir(base, 'anthropic/claude-4')\n→ s3://bucket/run_123/anthropic_claude-4"]
    GPT --> GH["CheckpointHook\n(gpt-5 config)"]
    Claude --> CH["CheckpointHook\n(claude-4 config)"]
    GH --> GC["s3://.../openai_gpt-5/\ncheckpoint_*.json.gz"]
    CH --> CC["s3://.../anthropic_claude-4/\ncheckpoint_*.json.gz"]
    GC & CC --> Merge["merge_logs([log_gpt, log_claude])\n→ combined EvalLog"]
```

---

## Dashboard Flow

```mermaid
flowchart TD
    U([User opens dashboard]) --> I[Enter S3/local path]
    I --> L["list_eval_logs(path)\nsorted by mtime desc"]
    L --> S{Checkpoints\nfound?}
    S -- No --> W["st.warning()\nNo checkpoints found"]
    S -- Yes --> SB["Sidebar: count of checkpoints"]
    SB --> SEL["Selectbox: pick checkpoint"]
    SEL --> R["read_eval_log(selected.name)"]
    R --> M["Display Metrics\nst.json(log.results)"]
    R --> SA["Display Samples\nlog.samples[:50]"]
    R --> T["Timeline chart\nsamples count over time"]
```
