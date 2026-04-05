from inspect_ai.hooks import EvalHook
from .checkpoint import CheckpointManager
from .resume import load_latest_checkpoint


class CheckpointHook(EvalHook):
    def __init__(self, config):
        self.manager = CheckpointManager(config)
        self.config = config

    async def on_eval_start(self, log, **kwargs):
        if self.config.resume:
            restored = load_latest_checkpoint(self.config.output_dir)
            if restored:
                log.samples = restored.samples
                log.results = restored.results

    async def on_sample_end(self, sample, log, **kwargs):
        if self.manager.should_checkpoint():
            self.manager.checkpoint(log)

    async def on_eval_end(self, log, **kwargs):
        self.manager.checkpoint(log)