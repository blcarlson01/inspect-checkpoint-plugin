import time

from inspect_ai.log import write_eval_log

from .utils import checkpoint_name


class CheckpointManager:
    def __init__(self, config):
        self.config = config
        self.last_checkpoint_time = time.time()

    def should_checkpoint(self) -> bool:
        return (time.time() - self.last_checkpoint_time) >= self.config.interval_seconds

    def checkpoint(self, log, step: int | None = None):
        if not self.config.enabled:
            return

        filename = checkpoint_name().replace(".json", ".json.gz")
        location = f"{self.config.output_dir}/{filename}"

        # Let inspect handle serialization, then compress via fsspec layer if needed
        write_eval_log(log, location=location)

        self.last_checkpoint_time = time.time()