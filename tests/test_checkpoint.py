import time
from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.checkpoint import CheckpointManager
from inspect_checkpoint_plugin.config import CheckpointConfig


def _make_manager(**kwargs):
    defaults = dict(
        interval_seconds=900,
        output_dir="s3://bucket/checkpoints",
        enabled=True,
        resume=True,
    )
    defaults.update(kwargs)
    config = CheckpointConfig(**defaults)
    return CheckpointManager(config)


# ── should_checkpoint ──────────────────────────────────────────────────────────

def test_should_checkpoint_false_immediately_after_creation():
    mgr = _make_manager(interval_seconds=900)
    assert mgr.should_checkpoint() is False


def test_should_checkpoint_true_after_interval_elapsed():
    mgr = _make_manager(interval_seconds=1)
    mgr.last_checkpoint_time = time.time() - 2
    assert mgr.should_checkpoint() is True


def test_should_checkpoint_true_at_exact_boundary():
    mgr = _make_manager(interval_seconds=5)
    mgr.last_checkpoint_time = time.time() - 5
    assert mgr.should_checkpoint() is True


def test_should_checkpoint_false_just_before_interval():
    mgr = _make_manager(interval_seconds=10)
    mgr.last_checkpoint_time = time.time() - 9
    assert mgr.should_checkpoint() is False


# ── checkpoint ─────────────────────────────────────────────────────────────────

def test_checkpoint_disabled_does_not_write():
    mgr = _make_manager(enabled=False)
    with patch("inspect_checkpoint_plugin.checkpoint.write_eval_log") as mock_write:
        mgr.checkpoint(MagicMock())
    mock_write.assert_not_called()


def test_checkpoint_calls_write_eval_log():
    mgr = _make_manager(enabled=True)
    mock_log = MagicMock()
    with (
        patch("inspect_checkpoint_plugin.checkpoint.write_eval_log") as mock_write,
        patch("inspect_checkpoint_plugin.utils.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.return_value = "20260405_120000"
        mgr.checkpoint(mock_log)
    mock_write.assert_called_once()
    args, kwargs = mock_write.call_args
    assert args[0] is mock_log


def test_checkpoint_location_format():
    mgr = _make_manager(
        output_dir="s3://bucket/checkpoints", enabled=True
    )
    captured = []

    def _capture(log, location=None):
        captured.append(location)

    with (
        patch("inspect_checkpoint_plugin.checkpoint.write_eval_log", side_effect=_capture),
        patch("inspect_checkpoint_plugin.utils.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.return_value = "20260405_120000"
        mgr.checkpoint(MagicMock())

    assert captured[0] == "s3://bucket/checkpoints/checkpoint_20260405_120000.json.gz"


def test_checkpoint_updates_last_checkpoint_time():
    mgr = _make_manager(enabled=True)
    mgr.last_checkpoint_time = 0

    with patch("inspect_checkpoint_plugin.checkpoint.write_eval_log"):
        before = time.time()
        mgr.checkpoint(MagicMock())
        after = time.time()

    assert before <= mgr.last_checkpoint_time <= after


def test_checkpoint_accepts_optional_step_argument():
    mgr = _make_manager(enabled=True)
    with patch("inspect_checkpoint_plugin.checkpoint.write_eval_log"):
        # Should not raise
        mgr.checkpoint(MagicMock(), step=42)
