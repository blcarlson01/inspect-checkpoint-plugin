"""
Integration tests: exercise multiple components together to verify
end-to-end correctness of the checkpoint -> resume pipeline.
"""
import asyncio
from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.checkpoint import CheckpointManager
from inspect_checkpoint_plugin.config import CheckpointConfig
from inspect_checkpoint_plugin.hooks import CheckpointHook
from inspect_checkpoint_plugin.resume import load_latest_checkpoint


# -- Round-trip path consistency -----------------------------------------------

def test_checkpoint_path_is_loadable_by_resume():
    """
    The path written by CheckpointManager.checkpoint() must be inside
    output_dir and end with .json.gz, so find_latest_checkpoint can retrieve it.
    """
    output_dir = "s3://bucket/checkpoints"
    config = CheckpointConfig(output_dir=output_dir, enabled=True)
    manager = CheckpointManager(config)

    written_locations: list[str] = []

    def capture_write(log, location: str | None = None) -> None:
        if location:
            written_locations.append(location)

    with (
        patch("inspect_checkpoint_plugin.checkpoint.write_eval_log", side_effect=capture_write),
        patch("inspect_checkpoint_plugin.utils.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.return_value = "20260405_120000"
        manager.checkpoint(MagicMock())

    assert len(written_locations) == 1
    written_location = written_locations[0]

    assert written_location.startswith(output_dir + "/")
    assert written_location.endswith(".json.gz")

    # Simulate resume: list_eval_logs returns an entry whose .name is the written path.
    mock_entry = MagicMock()
    mock_entry.mtime = 1743854400.0
    mock_entry.name = written_location
    mock_loaded = MagicMock()

    with (
        patch("inspect_checkpoint_plugin.resume.list_eval_logs", return_value=[mock_entry]),
        patch("inspect_checkpoint_plugin.resume.read_eval_log", return_value=mock_loaded) as mock_read,
    ):
        result = load_latest_checkpoint(output_dir)

    assert result is mock_loaded
    mock_read.assert_called_once_with(written_location)


# -- Full hook lifecycle --------------------------------------------------------

def test_full_hook_lifecycle_resume_then_task_end():
    """
    Simulates a complete eval run with the real Hooks API:
      on_task_start -> loads prior checkpoint; stores _prior_log
      on_task_end   -> writes exactly one final checkpoint

    Verifies that _prior_log is set and that the checkpoint is written to
    the correct output_dir.
    """
    config = CheckpointConfig(
        output_dir="s3://bucket/checkpoints",
        interval_seconds=0,
        enabled=True,
        resume=True,
    )
    hook = CheckpointHook(config)

    mock_restored = MagicMock()
    mock_restored.samples = [{"id": 0}]
    mock_restored.results = {"accuracy": 0.5}

    mock_task_end = MagicMock()
    mock_task_end.log = MagicMock()

    checkpoint_locations: list[str] = []

    def capture_write(log, location: str | None = None) -> None:
        if location:
            checkpoint_locations.append(location)

    with (
        patch("inspect_checkpoint_plugin.hooks.load_latest_checkpoint", return_value=mock_restored),
        patch("inspect_checkpoint_plugin.checkpoint.write_eval_log", side_effect=capture_write),
    ):
        asyncio.run(hook.on_task_start(MagicMock()))
        assert hook._prior_log is mock_restored

        asyncio.run(hook.on_task_end(mock_task_end))

    # Exactly one checkpoint written at task_end
    assert len(checkpoint_locations) == 1
    assert checkpoint_locations[0].startswith("s3://bucket/checkpoints/")
    assert checkpoint_locations[0].endswith(".json.gz")


def test_full_hook_lifecycle_no_resume_when_disabled():
    """
    When resume=False, on_task_start must not call load_latest_checkpoint
    and _prior_log must remain None.
    """
    config = CheckpointConfig(
        output_dir="s3://bucket/checkpoints",
        enabled=True,
        resume=False,
    )
    hook = CheckpointHook(config)

    with patch("inspect_checkpoint_plugin.hooks.load_latest_checkpoint") as mock_load:
        asyncio.run(hook.on_task_start(MagicMock()))

    mock_load.assert_not_called()
    assert hook._prior_log is None


def test_full_hook_lifecycle_disabled_writes_nothing():
    """
    When enabled=False the checkpoint manager must never call write_eval_log,
    including the mandatory on_task_end checkpoint.
    """
    config = CheckpointConfig(
        output_dir="s3://bucket/checkpoints",
        interval_seconds=0,
        enabled=False,
        resume=False,
    )
    hook = CheckpointHook(config)

    with patch("inspect_checkpoint_plugin.checkpoint.write_eval_log") as mock_write:
        asyncio.run(hook.on_task_start(MagicMock()))
        asyncio.run(hook.on_task_end(MagicMock()))

    mock_write.assert_not_called()
