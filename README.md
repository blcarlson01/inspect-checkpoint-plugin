# Inspect Checkpoint Plugin

A production-ready checkpointing, resume, and observability plugin for Inspect AI.

## 🚀 Features

- ⏱️ Automatic checkpointing every N minutes
- ☁️ Native S3 (or any fsspec backend) support
- 🔁 Resume from latest checkpoint
- 🧠 Multi-model run isolation + recovery
- 🗜️ Compression (`.json.gz`)
- 📊 Live Streamlit dashboard
- 🔒 Safe, append-only writes (no corruption)

---

## 📦 Installation

### Local development
```bash
pip install -e .
````

### From package (after publishing)

```bash
pip install inspect-checkpoint-plugin
```

---

## ⚙️ Basic Usage

```python
from inspect_ai import eval
from inspect_checkpoint_plugin import create_checkpoint_hook

hook = create_checkpoint_hook(
    interval_seconds=900,  # 15 minutes
    output_dir="s3://my-bucket/run_123/checkpoints",
)

eval(
    task,
    model=model,
    hooks=[hook],
)
```

---

## ☁️ S3 Setup

Ensure AWS credentials are configured:

```bash
export AWS_PROFILE=my-profile
# or
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

---

## 🗜️ Compression

Compression is automatic using `.json.gz`.

Output example:

```
s3://bucket/run_123/checkpoints/
  checkpoint_20260405_120000.json.gz
  checkpoint_20260405_121500.json.gz
```

---

## 🔁 Resume Support

Automatically resumes from the latest checkpoint:

```python
hook = create_checkpoint_hook(
    interval_seconds=900,
    output_dir="s3://my-bucket/run_123/checkpoints",
    resume=True,
)
```

### How it works

* Finds latest checkpoint in directory
* Restores:

  * samples
  * results
* Continues evaluation safely

---

## 🤖 Multi-Model Runs

Separate checkpoints per model:

```python
from inspect_checkpoint_plugin.multi_model import model_subdir

hook = create_checkpoint_hook(
    output_dir=model_subdir(
        "s3://my-bucket/run_123",
        model.name
    )
)
```

### Output structure

```
s3://bucket/run_123/
  gpt-5/
    checkpoints/
  claude-4/
    checkpoints/
```

---

## 🔄 Merging Multi-Model Logs

```python
from inspect_checkpoint_plugin.multi_model import merge_logs
from inspect_ai.log import list_eval_logs, read_eval_log

logs = [
    read_eval_log(l.location)
    for l in list_eval_logs("s3://bucket/run_123/gpt-5")
]

merged = merge_logs(logs)
```

---

## 📊 Live Dashboard

### Run dashboard

```bash
inspect-checkpoint-dashboard
```

or:

```bash
streamlit run inspect_checkpoint_plugin/dashboard/app.py
```

### Features

* Browse checkpoints
* View metrics
* Inspect samples
* Timeline of progress

### Example usage

Enter:

```
s3://my-bucket/run_123/checkpoints
```

---

## 🧪 Advanced Usage

### Custom interval (5 minutes)

```python
hook = create_checkpoint_hook(
    interval_seconds=300,
    output_dir="s3://bucket/run/checkpoints"
)
```

---

### Disable checkpointing

```python
hook = create_checkpoint_hook(enabled=False)
```

---

### Local filesystem

```python
hook = create_checkpoint_hook(
    output_dir="file:///tmp/inspect_logs"
)
```

---

## 🔒 Safety Model

This plugin guarantees:

* ✅ No partial writes
* ✅ No file overwrites
* ✅ Only complete snapshots
* ✅ Resume from valid checkpoints only

---

## ⚠️ Known Limitations

* Resume does not yet support:

  * partial sample replay
  * distributed worker coordination
* Large logs may impact dashboard performance

---

## 🧠 Recommended Setup

```python
hook = create_checkpoint_hook(
    interval_seconds=900,
    output_dir=f"s3://bucket/inspect/{run_id}/checkpoints",
    resume=True,
)
```

Run with:

```bash
inspect eval my_task.py --log-shared
```

---

## 🛠️ Development

### Run tests (example)

```bash
pytest
```

### Format

```bash
black .
```

---

## 📄 License

MIT

````