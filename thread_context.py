"""
Lightweight in-memory session + preference store.

Tracks (a) which threads Clarion is actively engaged in, so it only replies to
follow-ups where it's been invited, and (b) each user's accessibility
preferences (reading level, translation language, auto alt-text).

Swap this for Redis/DB before production; the interface stays the same.
"""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_sessions: dict[str, str] = {}          # f"{channel}:{thread_ts}" -> session_id
_prefs: dict[str, dict[str, Any]] = {}  # user_id -> preferences

DEFAULT_PREFS: dict[str, Any] = {
    "reading_level": "plain",
    "language": None,
    "auto_alt_text": True,
}


class SessionStore:
    @staticmethod
    def _key(channel: str, thread_ts: str) -> str:
        return f"{channel}:{thread_ts}"

    def start_session(self, channel: str, thread_ts: str, session_id: str) -> None:
        with _lock:
            _sessions[self._key(channel, thread_ts)] = session_id

    def get_session(self, channel: str, thread_ts: str) -> str | None:
        with _lock:
            return _sessions.get(self._key(channel, thread_ts))


class PrefStore:
    def get(self, user_id: str) -> dict[str, Any]:
        with _lock:
            return {**DEFAULT_PREFS, **_prefs.get(user_id, {})}

    def set(self, user_id: str, **updates: Any) -> dict[str, Any]:
        with _lock:
            current = _prefs.setdefault(user_id, {})
            current.update({k: v for k, v in updates.items() if v is not None})
            return {**DEFAULT_PREFS, **current}


session_store = SessionStore()
pref_store = PrefStore()
