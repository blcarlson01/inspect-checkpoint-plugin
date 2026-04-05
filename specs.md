# Inspect Checkpoint Plugin - Technical Specification

## 1. Overview

This library provides a checkpointing and recovery system for Inspect AI evaluations.

Primary goals:
- Prevent data loss during long-running evals
- Enable resumability
- Support cloud-native storage (S3)
- Provide observability via dashboard

---

## 2. Core Components

### 2.1 CheckpointManager

**Responsibilities:**
- Track checkpoint intervals
- Trigger safe writes
- Generate unique checkpoint paths

**Key Methods:**
```python
should_checkpoint() -> bool
checkpoint(log, step=None)
````

---

### 2.2 CheckpointHook

Extends Inspect EvalHook.

**Lifecycle Hooks:**

* `on_eval_start`
* `on_sample_end`
* `on_eval_end`

**Behavior:**

* Resume from checkpoint (optional)
* Trigger checkpoint after sample completion
* Final checkpoint at eval end

---

### 2.3 Resume Module

**Functions:**

```python
find_latest_checkpoint(path: str)
load_latest_checkpoint(path: str)
```

**Behavior:**

* Lists logs via Inspect API
* Sorts by last modified timestamp
* Loads most recent valid log

---

### 2.4 Compression Layer

**Format:**

* gzip (`.json.gz`)

**Requirements:**

* Must preserve full JSON structure
* Must be readable by Inspect log reader

---

### 2.5 Multi-Model Support

**Design:**

* Separate directory per model
* Sanitized model names

**Functions:**

```python
model_subdir(base_path, model_name)
merge_logs(logs)
```

---

### 2.6 Dashboard

**Framework:**

* Streamlit

**Capabilities:**

* List checkpoints
* Load logs
* Display:

  * metrics
  * samples
  * timeline

---

## 3. Storage Model

### 3.1 Path Format

```
{output_dir}/checkpoint_{timestamp}.json.gz
```

### 3.2 Requirements

* Must support fsspec
* Must allow:

  * write
  * list
  * read

Supported backends:

* S3 (`s3://`)
* Local (`file://`)
* GCS (optional)

---

## 4. Safety Guarantees

### 4.1 Write Safety

* No in-place overwrites
* Each checkpoint is immutable
* Writes occur only at safe boundaries

### 4.2 Consistency

* Checkpoints contain:

  * complete sample list
  * consistent metrics
* No partial sample states allowed

### 4.3 Resume Safety

* Only latest valid checkpoint used
* No merging of partial logs during resume

---

## 5. Configuration Spec

```python
CheckpointConfig(
    interval_seconds: int,
    output_dir: str,
    enabled: bool,
    resume: bool
)
```

### Defaults

| Field            | Default |
| ---------------- | ------- |
| interval_seconds | 900     |
| enabled          | True    |
| resume           | True    |

---

## 6. Hook Contract

### on_eval_start

* May mutate log
* Must not corrupt existing state

### on_sample_end

* Safe checkpoint boundary
* Must not block excessively

### on_eval_end

* Final snapshot required

---

## 7. Failure Modes

| Failure            | Behavior                |
| ------------------ | ----------------------- |
| S3 unavailable     | checkpoint skipped      |
| corrupt checkpoint | ignored on resume       |
| partial upload     | not reused              |
| large logs         | performance degradation |

---

## 8. Performance Characteristics

### Time Complexity

* Checkpoint write: O(n) where n = samples
* Resume load: O(n)

### Storage Growth

* Linear with checkpoints
* Mitigation:

  * compression
  * retention policies (future)

---

## 9. Extensibility

Planned extensions:

* Distributed checkpoint coordination
* Incremental/delta checkpoints
* Retention policies
* Streaming logs

---

## 10. CLI Spec

### Dashboard

```bash
inspect-checkpoint-dashboard
```

### Future CLI (planned)

```bash
inspect-checkpoint merge
inspect-checkpoint resume
inspect-checkpoint clean
```

---

## 11. Compatibility

| Component  | Version  |
| ---------- | -------- |
| Python     | 3.9+     |
| Inspect AI | Latest   |
| fsspec     | Required |

---

## 12. Security Considerations

* Relies on environment credentials (AWS, etc.)
* No credential storage in logs
* Read-only dashboard

---

## 13. Testing Requirements

* Unit:

  * checkpoint creation
  * resume loading
* Integration:

  * S3 writes
  * multi-model isolation
* Failure:

  * interrupted writes
  * corrupt files

---

## 14. Non-Goals

* Real-time streaming logs
* Distributed locking
* Partial sample recovery

---

## 15. Definitions

| Term          | Meaning                       |
| ------------- | ----------------------------- |
| Checkpoint    | Snapshot of EvalLog           |
| Resume        | Continue eval from checkpoint |
| Safe boundary | End of sample execution       |
| Append-only   | Never overwrite existing data |

---