from .config import CheckpointConfig
from .hooks import CheckpointHook


def create_checkpoint_hook(
    interval_seconds: int = 900,
    output_dir: str | None = None,
    enabled: bool = True,
    resume: bool = True,
) -> "CheckpointHook":
    config = CheckpointConfig(
        interval_seconds=interval_seconds,
        output_dir=output_dir,
        enabled=enabled,
        resume=resume,
    )
    return CheckpointHook(config)


__all__ = ["create_checkpoint_hook", "CheckpointConfig", "CheckpointHook"]
