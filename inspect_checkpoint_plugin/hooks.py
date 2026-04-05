from inspect_ai.hooks import Hooks, TaskEnd, TaskStart

from .checkpoint import CheckpointManager
from .config import CheckpointConfig
from .resume import load_latest_checkpoint


class CheckpointHook(Hooks):
    def __init__(self, config: CheckpointConfig) -> None:
        self.manager = CheckpointManager(config)
        self.config = config
        # Populated by on_task_start when resume=True; available for callers to inspect.
        self._prior_log = None

    async def on_task_start(self, data: TaskStart) -> None:
        if self.config.resume and self.config.output_dir is not None:
            self._prior_log = load_latest_checkpoint(self.config.output_dir)

    async def on_task_end(self, data: TaskEnd) -> None:
        self.manager.checkpoint(data.log)
