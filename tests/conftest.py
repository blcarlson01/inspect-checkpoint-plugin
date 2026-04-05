"""
Global pytest configuration.

Mock the external ``inspect_ai`` package and ``streamlit`` so that the plugin
modules can be imported and tested without the real dependencies installed.
"""
import sys
from unittest.mock import MagicMock


class MockEvalHook:
    """Stand-in for ``inspect_ai.hooks.EvalHook`` that supports subclassing."""


_mock_inspect_ai = MagicMock()
_mock_inspect_ai_log = MagicMock()
_mock_inspect_ai_hooks = MagicMock()
_mock_inspect_ai_hooks.EvalHook = MockEvalHook

sys.modules["inspect_ai"] = _mock_inspect_ai
sys.modules["inspect_ai.log"] = _mock_inspect_ai_log
sys.modules["inspect_ai.hooks"] = _mock_inspect_ai_hooks
sys.modules["streamlit"] = MagicMock()
