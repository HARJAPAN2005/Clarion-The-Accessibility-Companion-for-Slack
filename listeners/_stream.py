"""
Defensive streaming helper.

Bolt 1.28+ exposes `say_stream`, whose returned stream object has grown a couple
of method names across patch releases. To keep the hackathon demo bulletproof,
`stream_reply` tries to stream and transparently falls back to a single `say()`
if anything about the streaming surface differs.
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
    """
    `runner(on_chunk)` should run the agent and call on_chunk(text) as output
    arrives, returning the final text. We stream it into Slack if we can.
    """
    if say_stream is not None:
        try:
            stream = say_stream(thread_ts=thread_ts) if thread_ts else say_stream()
            append = getattr(stream, "append", None) or getattr(stream, "update", None)
            finish = getattr(stream, "stop", None) or getattr(stream, "complete", None)
            if append:
                def send_chunk(chunk: str) -> None:
                    try:
                        append(markdown_text=chunk)
                    except TypeError:
                        append(chunk)
                final = runner(send_chunk)
                if finish:
                    finish()
                return final
        except Exception as exc:
            logger.warning("streaming unavailable, falling back to say(): %s", exc)

    # Fallback: run to completion, post once.
    collected: list[str] = []
    final = runner(lambda chunk: collected.append(chunk))
    text = final or "".join(collected)
    say(text=text, thread_ts=thread_ts) if thread_ts else say(text=text)
    return text
