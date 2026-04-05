import asyncio
from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.config import CheckpointConfig
from inspect_checkpoint_plugin.hooks import CheckpointHook


def _make_hook(**kwargs):
    defaults = dict(
        interval_seconds=900,
        output_dir="s3://bucket/checkpoints",
        enabled=True,
        resume=True,
    )
    defaults.update(kwargs)
    config = CheckpointConfig(**defaults)
    return CheckpointHook(config)


# ── on_eval_start ──────────────────────────────────────────────────────────────

def test_on_eval_start_restores_samples_and_results_when_resume_enabled():
    hook = _make_hook(resume=True)
    mock_log = MagicMock()
    mock_restored = MagicMock()
    mock_restored.samples = [{"id": 1}]
    mock_restored.results = {"accuracy": 0.9}

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint",
        return_value=mock_restored,
    ):
        asyncio.run(hook.on_eval_start(mock_log))

    assert mock_log.samples == mock_restored.samples
    assert mock_log.results == mock_restored.results


def test_on_eval_start_no_op_when_no_checkpoint_exists():
    hook = _make_hook(resume=True)
    mock_log = MagicMock()
    original_samples = mock_log.samples

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint", return_value=None
    ):
        asyncio.run(hook.on_eval_start(mock_log))

    # Log should be untouched
    assert mock_log.samples == original_samples


def test_on_eval_start_skips_load_when_resume_disabled():
    hook = _make_hook(resume=False)
    mock_log = MagicMock()

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint"
    ) as mock_load:
        asyncio.run(hook.on_eval_start(mock_log))

    mock_load.assert_not_called()


# ── on_sample_end ──────────────────────────────────────────────────────────────

def test_on_sample_end_checkpoints_when_interval_reached():
    hook = _make_hook()

    with (
        patch.object(hook.manager, "should_checkpoint", return_value=True),
        patch.object(hook.manager, "checkpoint") as mock_ckpt,
    ):
        asyncio.run(hook.on_sample_end(MagicMock(), MagicMock()))

    mock_ckpt.assert_called_once()


def test_on_sample_end_passes_log_to_checkpoint():
    hook = _make_hook()
    mock_log = MagicMock()

    with (
        patch.object(hook.manager, "should_checkpoint", return_value=True),
        patch.object(hook.manager, "checkpoint") as mock_ckpt,
    ):
        asyncio.run(hook.on_sample_end(MagicMock(), mock_log))

    mock_ckpt.assert_called_once_with(mock_log)


def test_on_sample_end_skips_checkpoint_when_interval_not_reached():
    hook = _make_hook()

    with (
        patch.object(hook.manager, "should_checkpoint", return_value=False),
        patch.object(hook.manager, "checkpoint") as mock_ckpt,
    ):
        asyncio.run(hook.on_sample_end(MagicMock(), MagicMock()))

    mock_ckpt.assert_not_called()


# ── on_eval_end ────────────────────────────────────────────────────────────────

def test_on_eval_end_always_checkpoints():
    hook = _make_hook()
    mock_log = MagicMock()

    with patch.object(hook.manager, "checkpoint") as mock_ckpt:
        asyncio.run(hook.on_eval_end(mock_log))

    mock_ckpt.assert_called_once_with(mock_log)


def test_on_eval_end_checkpoints_even_when_disabled():
    # The hook itself always calls manager.checkpoint(); the manager respects enabled flag.
    hook = _make_hook(enabled=False)
    mock_log = MagicMock()

    with patch.object(hook.manager, "checkpoint") as mock_ckpt:
        asyncio.run(hook.on_eval_end(mock_log))

    mock_ckpt.assert_called_once_with(mock_log)
