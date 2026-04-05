from unittest.mock import MagicMock

from inspect_checkpoint_plugin.multi_model import merge_logs, model_subdir


# ── model_subdir ───────────────────────────────────────────────────────────────

def test_model_subdir_simple_name():
    assert model_subdir("s3://bucket/run", "gpt-4") == "s3://bucket/run/gpt-4"


def test_model_subdir_replaces_slash():
    assert model_subdir("s3://bucket/run", "openai/gpt-4") == "s3://bucket/run/openai_gpt-4"


def test_model_subdir_replaces_colon():
    assert model_subdir("s3://bucket/run", "model:v2") == "s3://bucket/run/model_v2"


def test_model_subdir_replaces_slash_and_colon():
    assert (
        model_subdir("s3://bucket/run", "provider/model:v1")
        == "s3://bucket/run/provider_model_v1"
    )


def test_model_subdir_no_special_chars():
    result = model_subdir("s3://bucket/run", "claude-4")
    assert result == "s3://bucket/run/claude-4"


# ── merge_logs ─────────────────────────────────────────────────────────────────

def test_merge_logs_empty_list_returns_none():
    assert merge_logs([]) is None


def test_merge_logs_single_log_returned_unchanged():
    log = MagicMock()
    log.samples = [{"id": 1}, {"id": 2}]
    result = merge_logs([log])
    assert result is log
    assert result.samples == [{"id": 1}, {"id": 2}]


def test_merge_logs_combines_samples_from_two_logs():
    log1 = MagicMock()
    log1.samples = [{"id": 1}]
    log2 = MagicMock()
    log2.samples = [{"id": 2}]
    result = merge_logs([log1, log2])
    assert len(result.samples) == 2
    assert {"id": 1} in result.samples
    assert {"id": 2} in result.samples


def test_merge_logs_combines_samples_from_three_logs():
    log1 = MagicMock()
    log1.samples = [{"id": 1}, {"id": 2}]
    log2 = MagicMock()
    log2.samples = [{"id": 3}]
    log3 = MagicMock()
    log3.samples = [{"id": 4}, {"id": 5}]
    result = merge_logs([log1, log2, log3])
    assert len(result.samples) == 5


def test_merge_logs_handles_none_samples():
    log1 = MagicMock()
    log1.samples = None
    log2 = MagicMock()
    log2.samples = [{"id": 1}]
    result = merge_logs([log1, log2])
    assert {"id": 1} in result.samples


def test_merge_logs_returns_first_log_as_base():
    log1 = MagicMock()
    log1.samples = [{"id": 1}]
    log2 = MagicMock()
    log2.samples = [{"id": 2}]
    result = merge_logs([log1, log2])
    assert result is log1


def test_merge_logs_both_none_samples_produces_empty_list():
    log1 = MagicMock()
    log1.samples = None
    log2 = MagicMock()
    log2.samples = None
    result = merge_logs([log1, log2])
    assert result.samples == []


def test_model_subdir_consecutive_special_chars():
    # "org//model::v1" → slashes and colons each replaced with underscores
    result = model_subdir("s3://bucket/run", "org//model::v1")
    assert result == "s3://bucket/run/org__model__v1"
