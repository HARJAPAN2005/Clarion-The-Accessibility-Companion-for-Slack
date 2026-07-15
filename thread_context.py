"""
thread_context — In-memory session and per-user preference stores.

Tracks two things:

    1. **Session state** — which threads Clarion is actively engaged in, so
       it only replies to follow-ups where it has been explicitly invited.

    2. **User preferences** — each user's accessibility settings (reading
       level, output language, automatic alt-text generation).

Both stores are thread-safe and use a simple in-memory dictionary backed by
a ``threading.Lock``. This is appropriate for single-process deployments.

Scaling to multiple processes or replicas requires a shared store. The
``SessionStore`` and ``PrefStore`` classes define a clear interface — swap
the implementation body for Redis, a database, or any other backend without
changing any callers.

Example Redis migration (drop-in replacement):

    import redis

    _r = redis.Redis.from_url(os.environ["REDIS_URL"])

    class PrefStore:
        def get(self, user_id: str) -> dict[str, Any]:
            raw = _r.hgetall(f"clarion:prefs:{user_id}")
            return {**DEFAULT_PREFS, **{k.decode(): v.decode() for k, v in raw.items()}}

        def set(self, user_id: str, **updates: Any) -> dict[str, Any]:
            _r.hset(f"clarion:prefs:{user_id}", mapping=updates)
            return self.get(user_id)
"""

from __future__ import annotations

import threading
from typing import Any

_lock = threading.Lock()
_sessions: dict[str, str] = {}          # "{channel}:{thread_ts}" -> session_id
_prefs: dict[str, dict[str, Any]] = {}  # user_id -> preference dict

#: Default preferences applied to every user who has not customised Clarion.
DEFAULT_PREFS: dict[str, Any] = {
    "reading_level": "plain",
    "language": None,
    "auto_alt_text": True,
}


class SessionStore:
    """Thread-safe store tracking active Clarion conversation sessions.

    A session is created the first time Clarion responds in a thread. It
    ensures Clarion only replies to follow-up messages in threads where it
    has been explicitly invited.
    """

    @staticmethod
    def _key(channel: str, thread_ts: str) -> str:
        return f"{channel}:{thread_ts}"

    def start_session(self, channel: str, thread_ts: str, session_id: str) -> None:
        """Register a new active session for a thread.

        Args:
            channel: The Slack channel ID.
            thread_ts: The thread's root message timestamp.
            session_id: An opaque identifier for this session.
        """
        with _lock:
            _sessions[self._key(channel, thread_ts)] = session_id

    def get_session(self, channel: str, thread_ts: str) -> str | None:
        """Retrieve the session ID for a thread, or ``None`` if not active.

        Args:
            channel: The Slack channel ID.
            thread_ts: The thread's root message timestamp.

        Returns:
            The session ID string, or ``None`` if Clarion is not engaged
            in this thread.
        """
        with _lock:
            return _sessions.get(self._key(channel, thread_ts))


class PrefStore:
    """Thread-safe store for per-user accessibility preferences.

    Preferences are merged on top of ``DEFAULT_PREFS`` so every user always
    receives a complete preference dict regardless of how many settings they
    have customised.
    """

    def get(self, user_id: str) -> dict[str, Any]:
        """Return the merged preferences for a user.

        Args:
            user_id: The Slack user ID.

        Returns:
            A preference dict with all keys from ``DEFAULT_PREFS``,
            overridden by any values the user has set.
        """
        with _lock:
            return {**DEFAULT_PREFS, **_prefs.get(user_id, {})}

    def set(self, user_id: str, **updates: Any) -> dict[str, Any]:
        """Update one or more preferences for a user.

        ``None`` values in ``updates`` are silently ignored so callers can
        pass optional arguments without worrying about overwriting existing
        settings with ``None``.

        Args:
            user_id: The Slack user ID.
            **updates: Keyword arguments mapping preference keys to new values.

        Returns:
            The updated merged preference dict.
        """
        with _lock:
            current = _prefs.setdefault(user_id, {})
            current.update({k: v for k, v in updates.items() if v is not None})
            return {**DEFAULT_PREFS, **current}


session_store = SessionStore()
pref_store = PrefStore()
