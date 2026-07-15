"""
listeners._stream — Defensive streaming reply helper.

Bolt 1.28+ exposes ``say_stream``, whose API surface has evolved across patch
releases. ``stream_reply`` tries to stream text into Slack as it is generated
and transparently falls back to a single ``say()`` call if anything about the
streaming surface is unexpected.

This separation keeps all streaming concerns in one place so event handlers
stay clean regardless of which Bolt version is installed.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger("clarion.stream")


def stream_reply(
    say: Callable,
    say_stream: Callable | None,
    runner: Callable[[Callable[[str], None]], str],
    thread_ts: str | None = None,
) -> str:
    """Stream an agent response into Slack, falling back to a single post.

    ``runner`` should call its ``on_chunk`` argument with each text fragment
    as it arrives and return the complete final text. ``stream_reply`` wires
    those chunks into Bolt's streaming surface when available.

    Args:
        say: Bolt ``say`` callable for posting a complete message.
        say_stream: Bolt ``say_stream`` callable, or ``None`` when the Bolt
            version does not support streaming.
        runner: A callable that accepts an ``on_chunk`` callback and returns
            the full response text. Typically a lambda wrapping ``run_clarion``.
        thread_ts: Thread timestamp to reply into, or ``None`` for a new
            top-level message.

    Returns:
        The final complete response text.
    """
    if say_stream is not None:
        try:
            stream = say_stream(thread_ts=thread_ts) if thread_ts else say_stream()
            append = getattr(stream, "append", None) or getattr(stream, "update", None)
            finish = getattr(stream, "stop", None) or getattr(stream, "complete", None)
            if append:

                def _send_chunk(chunk: str) -> None:
                    try:
                        append(markdown_text=chunk)
                    except TypeError:
                        append(chunk)

                final = runner(_send_chunk)
                if finish:
                    finish()
                return final
        except Exception as exc:
            logger.warning(
                "Streaming unavailable; falling back to say(): %s", exc
            )

    # Fallback: buffer all chunks and post once.
    collected: list[str] = []
    final = runner(lambda chunk: collected.append(chunk))
    text = final or "".join(collected)
    if thread_ts:
        say(text=text, thread_ts=thread_ts)
    else:
        say(text=text)
    return text
