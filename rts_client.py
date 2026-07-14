"""
Real-Time Search (RTS) API client.

Clarion uses the RTS API to define acronyms and jargon using *live* workspace
context — so a newcomer who sees "RTS" or "the Q3 OKR doc" gets a definition
grounded in how the team actually uses the term, not a stale glossary.

The RTS endpoint/token are read from the environment. When they aren't set (or
the call fails), we fall back to a small in-memory workspace glossary so the demo
still shows the *shape* of a real-time-grounded answer.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("clarion.rts")

RTS_ENDPOINT = os.environ.get("SLACK_RTS_ENDPOINT", "https://slack.com/api/search.realtime")
RTS_TOKEN = os.environ.get("SLACK_RTS_TOKEN")

# Demo fallback so `define_term` always returns something meaningful.
_DEMO_GLOSSARY: dict[str, list[dict[str, str]]] = {
    "rts": [{"snippet": "RTS = Real-Time Search API, used by Clarion to ground definitions in live workspace context.", "source": "#eng-platform"}],
    "okr": [{"snippet": "OKRs are our quarterly Objectives and Key Results; the Q3 doc lives in the #planning canvas.", "source": "#planning"}],
    "p1": [{"snippet": "A P1 is our highest-severity incident — page on-call immediately and open a #incident channel.", "source": "#oncall"}],
    "eod": [{"snippet": "EOD here means 5pm in the owner's local timezone, not UTC.", "source": "#team-norms"}],
}


def realtime_search(query: str, channel_id: str = "", limit: int = 3) -> list[dict[str, str]]:
    """
    Return a list of {snippet, source} results relevant to `query`.

    Scopes to `channel_id` when provided so definitions reflect the local
    conversation rather than the whole workspace.
    """
    if RTS_TOKEN:
        try:
            import requests

            resp = requests.get(
                RTS_ENDPOINT,
                headers={"Authorization": f"Bearer {RTS_TOKEN}"},
                params={"query": query, "channel": channel_id, "count": limit},
                timeout=6,
            )
            data = resp.json()
            matches = data.get("messages", {}).get("matches", [])[:limit]
            results = [
                {"snippet": m.get("text", ""), "source": f"#{m.get('channel', {}).get('name', 'workspace')}"}
                for m in matches
            ]
            if results:
                return results
        except Exception as exc:
            logger.warning("RTS call failed, using demo glossary: %s", exc)

    # Fallback: demo glossary keyed by the term.
    key = query.strip().lower().lstrip("#")
    return _DEMO_GLOSSARY.get(key, [])
