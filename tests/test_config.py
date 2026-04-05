from inspect_checkpoint_plugin.config import CheckpointConfig


def test_defaults():
    config = CheckpointConfig()
    assert config.interval_seconds == 900
    assert config.output_dir is None
    assert config.enabled is True
    assert config.resume is True


def test_custom_interval():
    config = CheckpointConfig(interval_seconds=300)
    assert config.interval_seconds == 300


def test_custom_output_dir():
    config = CheckpointConfig(output_dir="s3://bucket/path")
    assert config.output_dir == "s3://bucket/path"


def test_disabled():
    config = CheckpointConfig(enabled=False)
    assert config.enabled is False


def test_no_resume():
    config = CheckpointConfig(resume=False)
    assert config.resume is False


def test_all_custom_values():
    config = CheckpointConfig(
        interval_seconds=60,
        output_dir="file:///tmp/chk",
        enabled=False,
        resume=False,
    )
    assert config.interval_seconds == 60
    assert config.output_dir == "file:///tmp/chk"
    assert config.enabled is False
    assert config.resume is False
