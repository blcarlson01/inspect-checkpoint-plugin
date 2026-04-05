def model_subdir(base_path: str, model_name: str) -> str:
    safe_name = model_name.replace("/", "_").replace(":", "_")
    return f"{base_path}/{safe_name}"


def merge_logs(logs):
    """Merge multiple eval logs into one combined log, concatenating samples."""
    if not logs:
        return None
    merged = logs[0]
    for log in logs[1:]:
        merged.samples = (merged.samples or []) + (log.samples or [])
    return merged