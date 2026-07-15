"""
config — Centralized configuration, constants, and AI client factories.

All environment variable reads and singleton AI client creation live here.
Import from this module everywhere else to avoid duplication and ensure that
configuration changes propagate consistently across the entire codebase.

Environment variables (see .env.example for full documentation):
    OPENROUTER_API_KEY      Required for AI features. Falls back to offline mode.
    OPENROUTER_MODEL        Text model (default: poolside/laguna-xs-2.1:free).
    OPENROUTER_VISION_MODEL Vision model for image descriptions via OpenRouter.
    GEMINI_API_KEY          Preferred for vision; uses the Gemini API directly.
    SLACK_BOT_TOKEN         Required. Bot user OAuth token (xoxb-...).
    SLACK_APP_TOKEN         Required for Socket Mode (xapp-...).
    SLACK_RTS_TOKEN         Optional. Enables live Real-Time Search results.
    SLACK_RTS_ENDPOINT      Optional. Defaults to Slack's search.realtime API.
    SLACK_MCP_ENABLED       Set to "true" to use the Slack MCP Server path.
    SLACK_CLIENT_ID         Required only for HTTP + OAuth mode.
    SLACK_CLIENT_SECRET     Required only for HTTP + OAuth mode.
    SLACK_SIGNING_SECRET    Required only for HTTP + OAuth mode.
    SLACK_REDIRECT_URI      Required only for HTTP + OAuth mode.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("clarion.config")

# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------

#: Default text model used when OPENROUTER_MODEL is not set.
DEFAULT_MODEL: str = "poolside/laguna-xs-2.1:free"

#: Default vision model identifier when using the Gemini API directly.
DEFAULT_GEMINI_VISION_MODEL: str = "gemini-2.0-flash"

# ---------------------------------------------------------------------------
# Singleton AI client cache
# ---------------------------------------------------------------------------

_openai_client: Any = None
_gemini_client: Any = None


def get_openai_client() -> Any | None:
    """Return a cached OpenAI-compatible client pointed at OpenRouter.

    Returns ``None`` when ``OPENROUTER_API_KEY`` is not set, allowing all
    callers to degrade gracefully to their offline fallback.

    Returns:
        An ``openai.OpenAI`` instance configured for the OpenRouter base URL,
        or ``None`` if the key is missing or the package is unavailable.
    """
    global _openai_client
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    if _openai_client is None:
        try:
            from openai import OpenAI

            _openai_client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            logger.debug("OpenRouter client initialised.")
        except ImportError:
            logger.error(
                "The 'openai' package is not installed. Run: pip install openai"
            )
            return None
    return _openai_client


def get_gemini_client() -> Any | None:
    """Return a cached OpenAI-compatible client pointed at the Gemini API.

    Clarion uses this client for image descriptions because Gemini's vision
    models provide excellent image understanding. Falls back to an OpenRouter
    vision model when ``GEMINI_API_KEY`` is not set.

    Returns:
        An ``openai.OpenAI`` instance configured for the Gemini base URL,
        or ``None`` if ``GEMINI_API_KEY`` is missing or the package is
        unavailable.
    """
    global _gemini_client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    if _gemini_client is None:
        try:
            from openai import OpenAI

            _gemini_client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            logger.debug("Gemini client initialised.")
        except ImportError:
            logger.error(
                "The 'openai' package is not installed. Run: pip install openai"
            )
            return None
    return _gemini_client


# ---------------------------------------------------------------------------
# Settings snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of all Clarion configuration values.

    Use ``Settings.load()`` to read from environment variables. This class is
    intentionally simple — it is not a validator. Use it to pass configuration
    through the call stack without threading individual ``os.getenv`` calls
    everywhere.

    Attributes:
        openrouter_api_key: OpenRouter API key, or ``None`` if offline.
        openrouter_model: Text model identifier.
        openrouter_vision_model: Vision model identifier (OpenRouter path).
        gemini_api_key: Google Gemini API key, or ``None``.
        slack_bot_token: Slack bot OAuth token.
        slack_app_token: Slack app-level token (Socket Mode).
        slack_rts_token: Real-Time Search API token, or ``None``.
        slack_rts_endpoint: Real-Time Search API endpoint URL.
        slack_mcp_enabled: Whether to use the Slack MCP Server path.
        port: HTTP server port (for OAuth mode).
    """

    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_vision_model: str | None
    gemini_api_key: str | None
    slack_bot_token: str | None
    slack_app_token: str | None
    slack_rts_token: str | None
    slack_rts_endpoint: str
    slack_mcp_enabled: bool
    port: int

    @classmethod
    def load(cls) -> "Settings":
        """Read all settings from environment variables.

        Returns:
            A populated ``Settings`` instance.
        """
        return cls(
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
            openrouter_vision_model=os.environ.get("OPENROUTER_VISION_MODEL") or None,
            gemini_api_key=os.environ.get("GEMINI_API_KEY"),
            slack_bot_token=os.environ.get("SLACK_BOT_TOKEN"),
            slack_app_token=os.environ.get("SLACK_APP_TOKEN"),
            slack_rts_token=os.environ.get("SLACK_RTS_TOKEN"),
            slack_rts_endpoint=os.environ.get(
                "SLACK_RTS_ENDPOINT", "https://slack.com/api/search.realtime"
            ),
            slack_mcp_enabled=(
                os.environ.get("SLACK_MCP_ENABLED", "false").lower() == "true"
            ),
            port=int(os.environ.get("PORT", "3000")),
        )
