import gzip
import json
from io import BytesIO

def compress_log_data(log_dict: dict) -> bytes:
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(json.dumps(log_dict).encode("utf-8"))
    return buf.getvalue()