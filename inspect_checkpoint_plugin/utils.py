from datetime import datetime, timezone


def checkpoint_name() -> str:
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"checkpoint_{ts}.json"
