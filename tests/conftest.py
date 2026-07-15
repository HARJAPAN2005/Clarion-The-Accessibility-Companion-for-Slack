"""
Shared pytest fixtures for the Clarion test suite.

All fixtures that need to be accessible across multiple test modules are
defined here. pytest discovers this file automatically.
"""

from __future__ import annotations

import os
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from agent import ClarionDeps


@pytest.fixture(autouse=True)
def clear_env_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure AI API keys are not present during tests.

    This prevents tests from accidentally making real API calls when running
    in a developer environment that has keys configured.
    """
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture
def mock_slack_client() -> MagicMock:
    """Return a MagicMock configured to behave like a ``slack_sdk.WebClient``."""
    client = MagicMock()
    client.token = "xoxb-test-token"
    client.conversations_replies.return_value = {
        "messages": [
            {"user": "U111", "text": "We need to leverage our bandwidth to move the needle."},
            {"user": "U222", "text": "Agreed. Let's circle back by EOD and operationalize this."},
            {"user": "U111", "text": "The deliverable is due Friday. ASAP please."},
        ]
    }
    return client


@pytest.fixture
def sample_deps(mock_slack_client: MagicMock) -> ClarionDeps:
    """Return a ``ClarionDeps`` instance suitable for offline unit tests."""
    return ClarionDeps(
        client=mock_slack_client,
        user_id="U_TEST",
        channel_id="C_TEST",
        prefs={"reading_level": "plain", "language": None, "auto_alt_text": True},
    )


@pytest.fixture
def clear_config_singletons() -> Generator[None, None, None]:
    """Reset the cached AI client singletons between tests."""
    import config

    original_openai = config._openai_client
    original_gemini = config._gemini_client
    config._openai_client = None
    config._gemini_client = None
    yield
    config._openai_client = original_openai
    config._gemini_client = original_gemini
