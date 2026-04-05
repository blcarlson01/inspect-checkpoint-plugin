from inspect_checkpoint_plugin import CheckpointConfig, CheckpointHook, create_checkpoint_hook


def test_create_checkpoint_hook_returns_hook_instance():
    hook = create_checkpoint_hook()
    assert isinstance(hook, CheckpointHook)


def test_create_checkpoint_hook_default_interval():
    hook = create_checkpoint_hook()
    assert hook.config.interval_seconds == 900


def test_create_checkpoint_hook_custom_interval():
    hook = create_checkpoint_hook(interval_seconds=300)
    assert hook.config.interval_seconds == 300


def test_create_checkpoint_hook_custom_output_dir():
    hook = create_checkpoint_hook(output_dir="s3://bucket/path")
    assert hook.config.output_dir == "s3://bucket/path"


def test_create_checkpoint_hook_disabled():
    hook = create_checkpoint_hook(enabled=False)
    assert hook.config.enabled is False


def test_create_checkpoint_hook_default_enabled():
    hook = create_checkpoint_hook()
    assert hook.config.enabled is True


def test_create_checkpoint_hook_no_resume():
    hook = create_checkpoint_hook(resume=False)
    assert hook.config.resume is False


def test_create_checkpoint_hook_default_resume():
    hook = create_checkpoint_hook()
    assert hook.config.resume is True


def test_create_checkpoint_hook_config_is_checkpoint_config():
    hook = create_checkpoint_hook()
    assert isinstance(hook.config, CheckpointConfig)


def test_all_params_propagated():
    hook = create_checkpoint_hook(
        interval_seconds=60,
        output_dir="file:///tmp/ckpt",
        enabled=False,
        resume=False,
    )
    assert hook.config.interval_seconds == 60
    assert hook.config.output_dir == "file:///tmp/ckpt"
    assert hook.config.enabled is False
    assert hook.config.resume is False
