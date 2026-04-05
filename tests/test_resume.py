from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.resume import find_latest_checkpoint, load_latest_checkpoint


def test_find_latest_checkpoint_returns_none_when_no_logs():
    with patch("inspect_checkpoint_plugin.resume.list_eval_logs", return_value=[]):
        result = find_latest_checkpoint("s3://bucket/path")
    assert result is None


def test_find_latest_checkpoint_returns_most_recent():
    log1 = MagicMock()
    log1.last_modified = "2026-04-05T12:00:00"
    log2 = MagicMock()
    log2.last_modified = "2026-04-05T13:00:00"
    log3 = MagicMock()
    log3.last_modified = "2026-04-05T11:00:00"

    with patch(
        "inspect_checkpoint_plugin.resume.list_eval_logs",
        return_value=[log1, log2, log3],
    ):
        result = find_latest_checkpoint("s3://bucket/path")

    assert result is log2


def test_find_latest_checkpoint_single_log():
    log = MagicMock()
    log.last_modified = "2026-04-05T12:00:00"

    with patch(
        "inspect_checkpoint_plugin.resume.list_eval_logs", return_value=[log]
    ):
        result = find_latest_checkpoint("s3://bucket/path")

    assert result is log


def test_find_latest_checkpoint_passes_path():
    with patch(
        "inspect_checkpoint_plugin.resume.list_eval_logs", return_value=[]
    ) as mock_list:
        find_latest_checkpoint("s3://my-bucket/run/checkpoints")
    mock_list.assert_called_once_with("s3://my-bucket/run/checkpoints")


def test_load_latest_checkpoint_returns_none_when_no_logs():
    with patch(
        "inspect_checkpoint_plugin.resume.find_latest_checkpoint", return_value=None
    ):
        result = load_latest_checkpoint("s3://bucket/path")
    assert result is None


def test_load_latest_checkpoint_returns_loaded_log():
    mock_entry = MagicMock()
    mock_entry.location = "s3://bucket/path/checkpoint_20260405_120000.json.gz"
    mock_loaded = MagicMock()

    with (
        patch(
            "inspect_checkpoint_plugin.resume.find_latest_checkpoint",
            return_value=mock_entry,
        ),
        patch(
            "inspect_checkpoint_plugin.resume.read_eval_log",
            return_value=mock_loaded,
        ) as mock_read,
    ):
        result = load_latest_checkpoint("s3://bucket/path")

    assert result is mock_loaded
    mock_read.assert_called_once_with(mock_entry.location)
