"""Tests for the config module — client factories and Settings."""

from __future__ import annotations

import pytest


class TestGetOpenAIClient:
    def test_returns_none_without_key(self, clear_config_singletons: None) -> None:
        import config

        assert config.get_openai_client() is None

    def test_returns_client_with_key(
        self, monkeypatch: pytest.MonkeyPatch, clear_config_singletons: None
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        import config

        client = config.get_openai_client()
        assert client is not None

    def test_returns_same_instance_on_repeated_calls(
        self, monkeypatch: pytest.MonkeyPatch, clear_config_singletons: None
    ) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
        import config

        c1 = config.get_openai_client()
        c2 = config.get_openai_client()
        assert c1 is c2


class TestGetGeminiClient:
    def test_returns_none_without_key(self, clear_config_singletons: None) -> None:
        import config

        assert config.get_gemini_client() is None

    def test_returns_client_with_key(
        self, monkeypatch: pytest.MonkeyPatch, clear_config_singletons: None
    ) -> None:
        monkeypatch.setenv("GEMINI_API_KEY", "AIza-test-key")
        import config

        client = config.get_gemini_client()
        assert client is not None


class TestSettings:
    def test_defaults_applied_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
        monkeypatch.delenv("SLACK_MCP_ENABLED", raising=False)
        monkeypatch.delenv("PORT", raising=False)

        from config import DEFAULT_MODEL, Settings

        s = Settings.load()
        assert s.openrouter_model == DEFAULT_MODEL
        assert s.slack_mcp_enabled is False
        assert s.port == 3000

    def test_env_overrides_applied(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")
        monkeypatch.setenv("SLACK_MCP_ENABLED", "true")
        monkeypatch.setenv("PORT", "8080")

        from config import Settings

        s = Settings.load()
        assert s.openrouter_model == "openai/gpt-4o"
        assert s.slack_mcp_enabled is True
        assert s.port == 8080

    def test_settings_is_immutable(self) -> None:
        from config import Settings

        s = Settings.load()
        with pytest.raises((AttributeError, TypeError)):
            s.port = 9999  # type: ignore[misc]
