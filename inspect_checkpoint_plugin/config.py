from dataclasses import dataclass


@dataclass
class CheckpointConfig:
    interval_seconds: int = 900
    output_dir: str = None
    enabled: bool = True
    resume: bool = True