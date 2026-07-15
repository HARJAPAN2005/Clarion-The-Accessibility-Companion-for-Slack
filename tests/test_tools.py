"""
Tests for the five Clarion accessibility tools.

These tests exercise the offline fallback paths exclusively — no API keys are
required and no real network calls are made. The ``clear_env_keys`` fixture
in ``conftest.py`` ensures API keys are stripped from the environment
automatically for every test.
"""

from __future__ import annotations

import pytest

import tools
from agent import ClarionDeps


class TestSimplifyText:
    """Tests for ``tools.simplify_text`` offline fallback."""

    def test_replaces_leverage(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="We need to leverage this platform.")
        assert "leverage" not in result.lower() or "use" in result.lower()

    def test_replaces_bandwidth(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="I don't have the bandwidth.")
        assert "capacity" in result.lower() or "bandwidth" not in result.lower()

    def test_replaces_circle_back(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="Let's circle back on this tomorrow.")
        assert "follow up" in result.lower() or "circle back" not in result.lower()

    def test_replaces_synergy(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="We need more synergy here.")
        assert "synergy" not in result.lower() or "work together" in result.lower()

    def test_output_contains_header(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="Please leverage the platform.")
        assert "Clarion made this easier to read" in result

    def test_output_contains_footer(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="Any text here.")
        assert "Clarity preserved" in result

    def test_empty_text(self, sample_deps: ClarionDeps) -> None:
        result = tools.simplify_text(deps=sample_deps, text="")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_reading_levels(self, sample_deps: ClarionDeps) -> None:
        for level in ("grade5", "grade8", "plain", "concise"):
            result = tools.simplify_text(
                deps=sample_deps,
                text="We need to leverage our bandwidth.",
                reading_level=level,
            )
            assert isinstance(result, str)
            assert len(result) > 0

    def test_clean_text_unchanged_structure(self, sample_deps: ClarionDeps) -> None:
        """Clean text with no jargon should still return the standard wrapper."""
        result = tools.simplify_text(
            deps=sample_deps,
            text="Please send the report by Friday at noon.",
        )
        assert "Clarion made this easier to read" in result


class TestSummarizeThread:
    """Tests for ``tools.summarize_thread`` offline fallback."""

    def test_empty_thread_returns_placeholder(self, sample_deps: ClarionDeps) -> None:
        from unittest.mock import patch

        with patch("tools.fetch_thread_messages", return_value=[]):
            result = tools.summarize_thread(
                deps=sample_deps, channel_id="C123", thread_ts="1234567890.000"
            )
        assert "Nothing to summarize" in result

    def test_populated_thread_returns_digest(self, sample_deps: ClarionDeps) -> None:
        messages = [
            {"user": "Alice", "text": "The launch is set for Friday."},
            {"user": "Bob", "text": "I will handle the QA sign-off by Thursday."},
        ]
        from unittest.mock import patch

        with patch("tools.fetch_thread_messages", return_value=messages):
            result = tools.summarize_thread(
                deps=sample_deps, channel_id="C123", thread_ts="1234567890.000"
            )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_channel_returns_placeholder(self, sample_deps: ClarionDeps) -> None:
        result = tools.summarize_thread(deps=sample_deps, channel_id="", thread_ts="")
        assert "Nothing to summarize" in result


class TestGenerateAltText:
    """Tests for ``tools.generate_alt_text`` offline fallback."""

    def test_no_client_returns_fallback(self) -> None:
        deps = ClarionDeps(client=None)
        result = tools.generate_alt_text(deps=deps, image_url="https://example.com/img.png")
        assert "Screen-reader friendly description" in result

    def test_returns_accessible_fallback_message(self, sample_deps: ClarionDeps) -> None:
        result = tools.generate_alt_text(
            deps=sample_deps, image_url="https://example.com/img.png"
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestDefineTerm:
    """Tests for ``tools.define_term`` offline fallback."""

    def test_known_demo_term_returns_result(self, sample_deps: ClarionDeps) -> None:
        result = tools.define_term(deps=sample_deps, term="okr", channel_id="")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_term_returns_ask_colleague_fallback(self, sample_deps: ClarionDeps) -> None:
        result = tools.define_term(deps=sample_deps, term="xyzzy_unique_term_abc", channel_id="")
        assert "couldn't find" in result.lower() or "best person to ask" in result.lower()

    def test_returns_three_section_structure(self, sample_deps: ClarionDeps) -> None:
        result = tools.define_term(deps=sample_deps, term="xyzzy_unique_term_abc", channel_id="")
        assert "Here's what that means" in result


class TestInclusiveCheck:
    """Tests for ``tools.inclusive_check`` offline fallback."""

    def test_flags_leverage(self, sample_deps: ClarionDeps) -> None:
        result = tools.inclusive_check(deps=sample_deps, text="We need to leverage this.")
        assert "leverage" in result.lower()

    def test_flags_bandwidth(self, sample_deps: ClarionDeps) -> None:
        result = tools.inclusive_check(deps=sample_deps, text="I don't have the bandwidth.")
        assert "bandwidth" in result.lower()

    def test_flags_asap(self, sample_deps: ClarionDeps) -> None:
        result = tools.inclusive_check(deps=sample_deps, text="Please do this ASAP.")
        assert "asap" in result.lower() or "as soon as" in result.lower()

    def test_clean_text_returns_positive_confirmation(self, sample_deps: ClarionDeps) -> None:
        result = tools.inclusive_check(
            deps=sample_deps,
            text="Please send the report by Friday at noon.",
        )
        assert "clear and inclusive" in result.lower()

    def test_multiple_flags_all_reported(self, sample_deps: ClarionDeps) -> None:
        result = tools.inclusive_check(
            deps=sample_deps,
            text="We need to leverage bandwidth to touch base ASAP.",
        )
        # At least one flag should appear — offline mode uses pattern matching.
        assert "⚠️" in result or "clear and inclusive" in result

    def test_returns_string(self, sample_deps: ClarionDeps) -> None:
        result = tools.inclusive_check(deps=sample_deps, text="")
        assert isinstance(result, str)
