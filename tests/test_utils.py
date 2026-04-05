import re
from unittest.mock import MagicMock, patch

from inspect_checkpoint_plugin.utils import checkpoint_name


def test_checkpoint_name_starts_with_prefix():
    assert checkpoint_name().startswith("checkpoint_")


def test_checkpoint_name_ends_with_json():
    assert checkpoint_name().endswith(".json")


def test_checkpoint_name_timestamp_format():
    name = checkpoint_name()
    assert re.match(r"^checkpoint_\d{8}_\d{6}\.json$", name)


def test_checkpoint_name_uses_utc_datetime():
    mock_dt = MagicMock()
    mock_dt.now.return_value.strftime.return_value = "20260405_120000"
    with patch("inspect_checkpoint_plugin.utils.datetime", mock_dt):
        name = checkpoint_name()
    assert name == "checkpoint_20260405_120000.json"
    # Verify that now() was called with the UTC timezone argument
    mock_dt.now.assert_called_once()
    call_kwargs = mock_dt.now.call_args
    assert "tz" in call_kwargs.kwargs or len(call_kwargs.args) == 1
