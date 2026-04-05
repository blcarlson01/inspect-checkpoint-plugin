import asyncio
from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.config import CheckpointConfig
from inspect_checkpoint_plugin.hooks import CheckpointHook


def _make_hook(
    interval_seconds: int = 900,
    output_dir: str | None = "s3://bucket/checkpoints",
    enabled: bool = True,
    resume: bool = True,
) -> CheckpointHook:
    config = CheckpointConfig(
        interval_seconds=interval_seconds,
        output_dir=output_dir,
        enabled=enabled,
        resume=resume,
    )
    return CheckpointHook(config)


# ── initial state ──────────────────────────────────────────────────────────────

def test_prior_log_is_none_by_default():
    hook = _make_hook()
    assert hook._prior_log is None


# ── on_task_start ──────────────────────────────────────────────────────────────

def test_on_task_start_calls_load_when_resume_enabled():
    hook = _make_hook(resume=True)
    mock_restored = MagicMock()

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint",
        return_value=mock_restored,
    ) as mock_load:
        asyncio.run(hook.on_task_start(MagicMock()))

    mock_load.assert_called_once_with("s3://bucket/checkpoints")


def test_on_task_start_stores_prior_log():
    hook = _make_hook(resume=True)
    mock_restored = MagicMock()

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint",
        return_value=mock_restored,
    ):
        asyncio.run(hook.on_task_start(MagicMock()))

    assert hook._prior_log is mock_restored


def test_on_task_start_stores_none_when_no_checkpoint_found():
    hook = _make_hook(resume=True)

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint", return_value=None
    ):
        asyncio.run(hook.on_task_start(MagicMock()))

    assert hook._prior_log is None


def test_on_task_start_skips_load_when_resume_disabled():
    hook = _make_hook(resume=False)

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint"
    ) as mock_load:
        asyncio.run(hook.on_task_start(MagicMock()))

    mock_load.assert_not_called()
    assert hook._prior_log is None


# ── on_task_end ────────────────────────────────────────────────────────────────

def test_on_task_end_calls_checkpoint_with_log():
    hook = _make_hook()
    mock_data = MagicMock()

    with patch.object(hook.manager, "checkpoint") as mock_ckpt:
        asyncio.run(hook.on_task_end(mock_data))

    mock_ckpt.assert_called_once_with(mock_data.log)


def test_on_task_end_uses_log_from_data():
    hook = _make_hook()
    mock_data = MagicMock()
    mock_log = MagicMock()
    mock_data.log = mock_log

    with patch.object(hook.manager, "checkpoint") as mock_ckpt:
        asyncio.run(hook.on_task_end(mock_data))

    mock_ckpt.assert_called_once_with(mock_log)


def test_on_task_end_checkpoints_even_when_enabled_is_false():
    # The hook always calls manager.checkpoint(); the manager respects enabled flag.
    hook = _make_hook(enabled=False)
    mock_data = MagicMock()

    with patch.object(hook.manager, "checkpoint") as mock_ckpt:
        asyncio.run(hook.on_task_end(mock_data))

    mock_ckpt.assert_called_once_with(mock_data.log)
