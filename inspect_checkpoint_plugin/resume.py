from inspect_ai.log import list_eval_logs, read_eval_log

def find_latest_checkpoint(path: str):
    logs = list_eval_logs(path)
    if not logs:
        return None

    # Sort by mtime descending (mtime is float | None)
    logs = sorted(logs, key=lambda x: x.mtime or 0.0, reverse=True)
    return logs[0]


def load_latest_checkpoint(path: str):
    latest = find_latest_checkpoint(path)
    if not latest:
        return None

    return read_eval_log(latest.name)