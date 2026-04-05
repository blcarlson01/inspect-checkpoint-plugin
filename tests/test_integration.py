"""
Integration tests: exercise multiple components together to verify
end-to-end correctness of the checkpoint → resume pipeline.
"""
import asyncio
from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.checkpoint import CheckpointManager
from inspect_checkpoint_plugin.config import CheckpointConfig
from inspect_checkpoint_plugin.hooks import CheckpointHook
from inspect_checkpoint_plugin.resume import load_latest_checkpoint


# ── Round-trip path consistency ───────────────────────────────────────────────

def test_checkpoint_path_is_loadable_by_resume():
    """
    The path written by CheckpointManager.checkpoint() must be within the
    output_dir so that find_latest_checkpoint(output_dir) can discover it,
    and it must end with .json.gz as required by the storage spec.
    """
    output_dir = "s3://bucket/checkpoints"
    config = CheckpointConfig(output_dir=output_dir, enabled=True)
    manager = CheckpointManager(config)

    written_locations = []

    def capture_write(log, location=None):
        written_locations.append(location)

    with (
        patch("inspect_checkpoint_plugin.checkpoint.write_eval_log", side_effect=capture_write),
        patch("inspect_checkpoint_plugin.utils.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.return_value = "20260405_120000"
        manager.checkpoint(MagicMock())

    assert len(written_locations) == 1
    written_location = written_locations[0]

    # Path must be inside output_dir and be a .json.gz file
    assert written_location.startswith(output_dir + "/")
    assert written_location.endswith(".json.gz")

    # Simulate resume: list_eval_logs returns an entry at the exact written location
    mock_entry = MagicMock()
    mock_entry.last_modified = "2026-04-05T12:00:00"
    mock_entry.location = written_location
    mock_loaded = MagicMock()

    with (
        patch("inspect_checkpoint_plugin.resume.list_eval_logs", return_value=[mock_entry]),
        patch("inspect_checkpoint_plugin.resume.read_eval_log", return_value=mock_loaded) as mock_read,
    ):
        result = load_latest_checkpoint(output_dir)

    assert result is mock_loaded
    mock_read.assert_called_once_with(written_location)


# ── Full hook lifecycle ───────────────────────────────────────────────────────

def test_full_hook_lifecycle_resume_then_samples_then_end():
    """
    Simulates a complete eval run:
      on_eval_start  → restores state from latest checkpoint
      on_sample_end  × 3 → checkpoints after each (interval_seconds=0)
      on_eval_end    → final mandatory checkpoint

    Verifies that resume mutates the log, that intermediate checkpoints fire,
    and that the final checkpoint is always written.
    """
    config = CheckpointConfig(
        output_dir="s3://bucket/checkpoints",
        interval_seconds=0,  # always checkpoint on sample_end
        enabled=True,
        resume=True,
    )
    hook = CheckpointHook(config)

    mock_log = MagicMock()
    mock_restored = MagicMock()
    mock_restored.samples = [{"id": 0}]
    mock_restored.results = {"accuracy": 0.5}

    checkpoint_locations = []

    def capture_write(log, location=None):
        checkpoint_locations.append(location)

    with (
        patch(
            "inspect_checkpoint_plugin.hooks.load_latest_checkpoint",
            return_value=mock_restored,
        ),
        patch(
            "inspect_checkpoint_plugin.checkpoint.write_eval_log",
            side_effect=capture_write,
        ),
    ):
        # Start: resume should fire
        asyncio.run(hook.on_eval_start(mock_log))
        assert mock_log.samples == mock_restored.samples
        assert mock_log.results == mock_restored.results

        # Three samples complete
        for _ in range(3):
            asyncio.run(hook.on_sample_end(MagicMock(), mock_log))

        # End: final checkpoint
        asyncio.run(hook.on_eval_end(mock_log))

    # 3 sample-end checkpoints + 1 eval-end checkpoint
    assert len(checkpoint_locations) == 4
    # All checkpoints must target the configured output_dir
    for loc in checkpoint_locations:
        assert loc.startswith("s3://bucket/checkpoints/")
        assert loc.endswith(".json.gz")


def test_full_hook_lifecycle_no_resume_when_disabled():
    """
    When resume=False, on_eval_start must not modify the log even if a
    checkpoint exists in the output directory.
    """
    config = CheckpointConfig(
        output_dir="s3://bucket/checkpoints",
        enabled=True,
        resume=False,
    )
    hook = CheckpointHook(config)

    mock_log = MagicMock()
    original_samples = mock_log.samples
    original_results = mock_log.results

    mock_restored = MagicMock()

    with patch(
        "inspect_checkpoint_plugin.hooks.load_latest_checkpoint",
        return_value=mock_restored,
    ) as mock_load:
        asyncio.run(hook.on_eval_start(mock_log))

    mock_load.assert_not_called()
    assert mock_log.samples == original_samples
    assert mock_log.results == original_results


def test_full_hook_lifecycle_disabled_writes_nothing():
    """
    When enabled=False the checkpoint manager must never call write_eval_log,
    including the mandatory on_eval_end checkpoint.
    """
    config = CheckpointConfig(
        output_dir="s3://bucket/checkpoints",
        interval_seconds=0,
        enabled=False,
        resume=False,
    )
    hook = CheckpointHook(config)

    with (
        patch(
            "inspect_checkpoint_plugin.checkpoint.write_eval_log"
        ) as mock_write,
    ):
        asyncio.run(hook.on_eval_start(MagicMock()))
        asyncio.run(hook.on_sample_end(MagicMock(), MagicMock()))
        asyncio.run(hook.on_eval_end(MagicMock()))

    mock_write.assert_not_called()
