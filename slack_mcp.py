"""
Slack MCP Server helper.

When Clarion runs via app_oauth.py with the Model Context Protocol toggle on,
thread history is read through the Slack MCP Server (the recommended, governed
path). For local Socket Mode development we fall back to the Web API
(`conversations.replies`) so the same tool works in both modes.

Both paths return a normalized list of {user, text} dicts.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("clarion.mcp")

USE_MCP = os.environ.get("SLACK_MCP_ENABLED", "false").lower() == "true"


def fetch_thread_messages(client: Any, channel_id: str, thread_ts: str) -> list[dict[str, str]]:
    if not channel_id or not thread_ts:
        return []

    if USE_MCP:
        try:
            return _fetch_via_mcp(channel_id, thread_ts)
        except Exception as exc:
            logger.warning("MCP fetch failed, falling back to Web API: %s", exc)

    return _fetch_via_web_api(client, channel_id, thread_ts)


def _fetch_via_web_api(client: Any, channel_id: str, thread_ts: str) -> list[dict[str, str]]:
    if client is None:
        return []
    try:
        resp = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=100)
        out = []
        for m in resp.get("messages", []):
            if m.get("subtype"):
                continue
            out.append({"user": m.get("user", "someone"), "text": m.get("text", "")})
        return out
    except Exception as exc:
        logger.warning("conversations.replies failed: %s", exc)
        return []


def _fetch_via_mcp(channel_id: str, thread_ts: str) -> list[dict[str, str]]:
    """
    Read thread history through the Slack MCP Server.

    The MCP client is provided by Bolt when the app runs in HTTP/OAuth mode with
    the Model Context Protocol toggle enabled (see README → 'Enable the Slack MCP
    Server'). This is the governed, enterprise-friendly path Slack recommends.
    """
    from slack_bolt.mcp import get_mcp_client  # provided by Bolt 1.28+ in OAuth mode

    mcp = get_mcp_client()
    result = mcp.call_tool(
        "conversations_replies",
        {"channel": channel_id, "ts": thread_ts, "limit": 100},
    )
    return [
        {"user": m.get("user", "someone"), "text": m.get("text", "")}
        for m in result.get("messages", [])
        if not m.get("subtype")
    ]
