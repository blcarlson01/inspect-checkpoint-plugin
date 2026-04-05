from unittest.mock import MagicMock, patch

# Import the module once so bindings are established before individual tests patch them
from inspect_checkpoint_plugin.dashboard import app
from inspect_checkpoint_plugin.dashboard.app import load_logs
import streamlit as st  # type: ignore[import-untyped]

def test_load_logs_returns_sorted_descending():
    log1 = MagicMock()
    log1.mtime = 1743854400.0
    log2 = MagicMock()
    log2.mtime = 1743858000.0
    log3 = MagicMock()
    log3.mtime = 1743850800.0

    with patch.object(app, "list_eval_logs", return_value=[log1, log2, log3]):
        result = load_logs("s3://bucket/path")

    assert result[0] is log2
    assert result[1] is log1
    assert result[2] is log3


def test_load_logs_empty():
    with patch.object(app, "list_eval_logs", return_value=[]):
        result = load_logs("s3://bucket/path")
    assert result == []


def test_main_with_logs_renders_metrics_and_samples():    

    mock_log = MagicMock()
    mock_log.results = {"accuracy": 0.9}
    mock_log.samples = [{"id": 1}, {"id": 2}]

    mock_entry = MagicMock()
    mock_entry.name = "s3://bucket/path/checkpoint_20260405_120000.json.gz"

    st.text_input.return_value = "s3://bucket/checkpoints"
    st.selectbox.return_value = mock_entry

    with (
        patch.object(app, "list_eval_logs", return_value=[mock_entry]),
        patch.object(app, "read_eval_log", return_value=mock_log),
    ):
        app.main()

    st.header.assert_called()
    st.json.assert_called_with(mock_log.results)


def test_main_shows_warning_when_no_logs():

    st.text_input.return_value = "s3://bucket/checkpoints"

    with patch.object(app, "list_eval_logs", return_value=[]):
        app.main()

    st.warning.assert_called()


def test_main_truncates_samples_display_to_50():

    mock_log = MagicMock()
    mock_log.results = {}
    mock_log.samples = [{"id": i} for i in range(60)]

    mock_entry = MagicMock()
    mock_entry.name = "s3://bucket/path/checkpoint_20260405_120000.json.gz"

    st.text_input.return_value = "s3://bucket/checkpoints"
    st.selectbox.return_value = mock_entry
    st.write.reset_mock()

    with (
        patch.object(app, "list_eval_logs", return_value=[mock_entry]),
        patch.object(app, "read_eval_log", return_value=mock_log),
    ):
        app.main()

    # st.write is called once per sample in the [:50] slice
    sample_writes = [
        c for c in st.write.call_args_list if c.args and isinstance(c.args[0], dict)
    ]
    assert len(sample_writes) == 50
