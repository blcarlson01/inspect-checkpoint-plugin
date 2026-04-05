import gzip
import json

from inspect_checkpoint_plugin.compression import compress_log_data


def test_returns_bytes():
    result = compress_log_data({"key": "value"})
    assert isinstance(result, bytes)


def test_output_is_valid_gzip():
    compressed = compress_log_data({"a": 1})
    # gzip.decompress raises on invalid data
    decompressed = gzip.decompress(compressed)
    assert decompressed is not None


def test_preserves_full_json_structure():
    data = {"key": "value", "nested": {"a": 1}, "list": [1, 2, 3]}
    compressed = compress_log_data(data)
    restored = json.loads(gzip.decompress(compressed).decode("utf-8"))
    assert restored == data


def test_empty_dict():
    compressed = compress_log_data({})
    restored = json.loads(gzip.decompress(compressed).decode("utf-8"))
    assert restored == {}


def test_unicode_data():
    data = {"message": "héllo wörld 你好"}
    compressed = compress_log_data(data)
    restored = json.loads(gzip.decompress(compressed).decode("utf-8"))
    assert restored == data


def test_large_payload():
    data = {"samples": list(range(10_000))}
    compressed = compress_log_data(data)
    restored = json.loads(gzip.decompress(compressed).decode("utf-8"))
    assert restored == data


def test_non_serializable_value_raises_type_error():
    import pytest
    with pytest.raises(TypeError):
        compress_log_data({"bad": object()})
