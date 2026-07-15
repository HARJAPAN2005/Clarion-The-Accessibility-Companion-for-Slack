"""Tests for the SessionStore and PrefStore classes in thread_context."""

from __future__ import annotations

import pytest

from thread_context import DEFAULT_PREFS, PrefStore, SessionStore


class TestSessionStore:
    def setup_method(self) -> None:
        self.store = SessionStore()

    def test_get_unknown_session_returns_none(self) -> None:
        assert self.store.get_session("C_UNKNOWN", "9999.0000") is None

    def test_start_and_get_session(self) -> None:
        self.store.start_session("C123", "1234.000", "session-abc")
        result = self.store.get_session("C123", "1234.000")
        assert result == "session-abc"

    def test_different_threads_isolated(self) -> None:
        self.store.start_session("C123", "1111.000", "s1")
        self.store.start_session("C123", "2222.000", "s2")
        assert self.store.get_session("C123", "1111.000") == "s1"
        assert self.store.get_session("C123", "2222.000") == "s2"

    def test_different_channels_isolated(self) -> None:
        self.store.start_session("C_ALPHA", "1111.000", "sa")
        self.store.start_session("C_BETA", "1111.000", "sb")
        assert self.store.get_session("C_ALPHA", "1111.000") == "sa"
        assert self.store.get_session("C_BETA", "1111.000") == "sb"

    def test_overwrite_session(self) -> None:
        self.store.start_session("C123", "1234.000", "session-old")
        self.store.start_session("C123", "1234.000", "session-new")
        assert self.store.get_session("C123", "1234.000") == "session-new"


class TestPrefStore:
    def setup_method(self) -> None:
        self.store = PrefStore()

    def test_get_unknown_user_returns_defaults(self) -> None:
        prefs = self.store.get("U_NEW_USER")
        assert prefs == DEFAULT_PREFS

    def test_set_reading_level(self) -> None:
        self.store.set("U123", reading_level="grade5")
        prefs = self.store.get("U123")
        assert prefs["reading_level"] == "grade5"

    def test_set_language(self) -> None:
        self.store.set("U123", language="Spanish")
        prefs = self.store.get("U123")
        assert prefs["language"] == "Spanish"

    def test_set_auto_alt_text(self) -> None:
        self.store.set("U123", auto_alt_text=False)
        prefs = self.store.get("U123")
        assert prefs["auto_alt_text"] is False

    def test_none_value_does_not_overwrite(self) -> None:
        self.store.set("U123", reading_level="grade8")
        self.store.set("U123", reading_level=None)  # type: ignore[arg-type]
        prefs = self.store.get("U123")
        assert prefs["reading_level"] == "grade8"

    def test_defaults_merged_with_user_prefs(self) -> None:
        self.store.set("U123", reading_level="concise")
        prefs = self.store.get("U123")
        # All default keys should still be present.
        for key in DEFAULT_PREFS:
            assert key in prefs

    def test_different_users_isolated(self) -> None:
        self.store.set("U_ALICE", reading_level="grade5")
        self.store.set("U_BOB", reading_level="concise")
        assert self.store.get("U_ALICE")["reading_level"] == "grade5"
        assert self.store.get("U_BOB")["reading_level"] == "concise"

    def test_set_returns_merged_prefs(self) -> None:
        result = self.store.set("U123", reading_level="grade8")
        assert "reading_level" in result
        assert "language" in result
        assert "auto_alt_text" in result
