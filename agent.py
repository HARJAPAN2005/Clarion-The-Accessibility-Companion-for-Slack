"""
agent — Clarion agent core.

Wraps an OpenAI-compatible chat completion loop (via OpenRouter) and exposes
five accessibility tools to the model. The agent decides which tool to call
based on the user's request and iterates until it produces a final text reply.

Tools available to the model:

    simplify_text      Plain-language rewrite of any message.
    summarize_thread   Catch-up digest of a Slack thread.
    generate_alt_text  Screen-reader description of an image.
    define_term        Live acronym/jargon lookup via Real-Time Search.
    inclusive_check    Flags exclusionary or jargon-heavy phrasing.

The agent loop is deliberately framework-thin so the same code path works in
Socket Mode (local dev) and HTTP+OAuth mode (production). An offline fallback
ensures Clarion stays useful even when AI services are unreachable.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

import tools
from config import DEFAULT_MODEL, get_openai_client

logger = logging.getLogger("clarion.agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are Clarion — the accessibility layer for Slack.
Your purpose is to make every workplace conversation easier to understand for \
everyone: people with dyslexia, ADHD, or cognitive differences; non-native \
English speakers; people who are blind or have low vision; and anyone joining \
a conversation late.

Your personality: calm, warm, helpful, and professional. You are a thoughtful \
teammate, not a chatbot.

Core principles:
- Plain language always. Short sentences. Common words. One idea per sentence.
- Never drop meaning. Preserve every decision, owner, date, number, and action item exactly.
- Never be condescending. You remove communication barriers — you don't simplify people.
- When describing an image: be specific enough that someone who cannot see it gets the full picture.
- When defining a term: treat the person as intelligent, just unfamiliar. Never make them feel \
they should already know.
- When checking a draft: be a supportive coach, not a critic. The writer is trying to \
communicate well.
- Respect the user's saved reading level and language preferences when provided.
- Never start a response with "Sure!", "Of course!", "Great question!", or "Certainly!".
- Never use jargon yourself. Clarion practises what it preaches.

Always choose the right tool. When someone pastes text without an explicit request, \
default to simplify_text.
Keep responses tight — this is a chat surface. Be useful, not verbose.\
"""

# ---------------------------------------------------------------------------
# Tool schema advertised to the model (OpenAI function-calling format)
# ---------------------------------------------------------------------------

TOOL_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "simplify_text",
            "description": (
                "Rewrite text into clear plain language at the requested reading level, "
                "preserving all meaning, decisions, owners, dates and action items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to simplify.",
                    },
                    "reading_level": {
                        "type": "string",
                        "enum": ["grade5", "grade8", "plain", "concise"],
                        "description": "Target reading level. Defaults to 'plain'.",
                    },
                    "language": {
                        "type": "string",
                        "description": (
                            "Optional ISO language name to translate the plain-language "
                            "version into."
                        ),
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_thread",
            "description": (
                "Produce a plain-language catch-up digest of a Slack thread: "
                "the decision, who owns what, deadlines, and open questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string"},
                    "thread_ts": {"type": "string"},
                },
                "required": ["channel_id", "thread_ts"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_alt_text",
            "description": (
                "Generate concise, useful screen-reader alt-text for an image, plus a longer "
                "description if the image is complex (a chart, diagram, or screenshot)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {"type": "string"},
                    "context": {
                        "type": "string",
                        "description": "Surrounding message text, if any.",
                    },
                },
                "required": ["image_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "define_term",
            "description": (
                "Define an acronym or piece of jargon using live Real-Time Search over "
                "workspace context and the web. Use for internal shorthand newcomers may "
                "not know."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "channel_id": {
                        "type": "string",
                        "description": (
                            "Channel where the term appeared, for workspace-scoped search."
                        ),
                    },
                },
                "required": ["term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inclusive_check",
            "description": (
                "Scan a draft message for jargon, idioms, unexplained acronyms, or "
                "exclusionary phrasing and suggest clearer alternatives before it is sent."
            ),
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Runtime dependencies container
# ---------------------------------------------------------------------------


@dataclass
class ClarionDeps:
    """Runtime dependencies passed through the agent and tool call chain.

    Attributes:
        client: A ``slack_sdk.WebClient`` instance for Slack API calls.
        user_id: The Slack user ID of the person who triggered the request.
        channel_id: The Slack channel ID where the request originated.
        prefs: Per-user accessibility preferences (reading level, language, etc.).
    """

    client: Any  # slack_sdk.WebClient — typed as Any to avoid import coupling
    user_id: str | None = None
    channel_id: str | None = None
    prefs: dict[str, Any] = field(default_factory=dict)


# Map tool names to their Python implementations in tools.py
_TOOL_IMPLS: dict[str, Callable[..., str]] = {
    "simplify_text": tools.simplify_text,
    "summarize_thread": tools.summarize_thread,
    "generate_alt_text": tools.generate_alt_text,
    "define_term": tools.define_term,
    "inclusive_check": tools.inclusive_check,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_tool(name: str, args: dict[str, Any], deps: ClarionDeps) -> str:
    """Dispatch a model-requested tool call to its Python implementation.

    Args:
        name: The tool name as declared in ``TOOL_SCHEMA``.
        args: Parsed keyword arguments from the model's JSON output.
        deps: Runtime dependencies (Slack client, user context, preferences).

    Returns:
        The tool's string output, ready to be fed back to the model.
    """
    impl = _TOOL_IMPLS.get(name)
    if impl is None:
        logger.warning("Unknown tool requested by model: %s", name)
        return f"(unknown tool: {name})"
    logger.info("tool_call name=%s args=%s", name, list(args.keys()))
    return impl(deps=deps, **args)


def _attempt_llm_call(
    client: Any,
    model: str,
    messages: list[dict[str, Any]],
    retries: int = 2,
) -> Any | None:
    """Attempt a streaming chat completion with exponential-backoff retry.

    Args:
        client: An OpenAI-compatible client instance.
        model: The model identifier string.
        messages: The full conversation history to send.
        retries: Number of additional attempts after the first failure.

    Returns:
        A streaming response object, or ``None`` on unrecoverable failure.

    Raises:
        APIError: Re-raised for 404 (model not found) so the caller can try
            a fallback model without masking the error.
    """
    for attempt in range(retries + 1):
        try:
            return client.chat.completions.create(
                model=model,
                max_tokens=1400,
                temperature=0.25,
                tools=TOOL_SCHEMA,
                messages=messages,
                stream=True,
            )
        except RateLimitError as exc:
            logger.warning(
                "Rate limited (429) on attempt %d/%d: %s",
                attempt + 1,
                retries + 1,
                exc,
            )
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            return None
        except APIError as exc:
            status = getattr(exc, "status_code", None)
            if status == 404:
                raise  # Let the caller handle model-not-found fallback.
            if status in (401, 403):
                logger.error("Authentication error (%s): %s", status, exc)
                return None
            if status in (408, 500, 502, 503, 504):
                logger.warning("Server error (%s) on attempt %d: %s", status, attempt + 1, exc)
                if attempt < retries:
                    time.sleep(2**attempt)
                    continue
                return None
            logger.error("Unexpected API error: %s", exc)
            return None
        except (APIConnectionError, APITimeoutError) as exc:
            logger.warning("Connection/timeout error on attempt %d: %s", attempt + 1, exc)
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            return None
        except Exception as exc:
            logger.exception("Unexpected error during streaming LLM call: %s", exc)
            return None
    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

#: Maximum number of agent loop iterations before giving up.
_MAX_ITERATIONS = 6


def run_clarion(
    prompt: str,
    deps: ClarionDeps,
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """Run one turn of the Clarion agent loop.

    The agent sends the user prompt to the model, handles any tool calls the
    model requests, and iterates until the model produces a final text reply.

    When ``on_chunk`` is provided, streamed text deltas are forwarded to it in
    real time so Bolt's ``say_stream`` can push partial output into Slack as
    it is generated.

    Args:
        prompt: The user's message or constructed prompt text.
        deps: Runtime dependencies (Slack client, user context, preferences).
        on_chunk: Optional callback receiving streamed text fragments.

    Returns:
        The final text response from the agent.
    """
    client = get_openai_client()
    if not client:
        logger.warning("No OpenRouter API key — using offline fallback.")
        result = tools.simplify_text(deps=deps, text=prompt)
        if on_chunk:
            on_chunk(result)
        return result

    configured_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for _ in range(_MAX_ITERATIONS):
        response = None
        try:
            response = _attempt_llm_call(client, configured_model, messages)
        except APIError as exc:
            if getattr(exc, "status_code", None) == 404 and configured_model != DEFAULT_MODEL:
                logger.info("Model not found; falling back to default: %s", DEFAULT_MODEL)
                try:
                    response = _attempt_llm_call(client, DEFAULT_MODEL, messages, retries=0)
                except Exception as inner:
                    logger.error("Default model fallback failed: %s", inner)

        if not response:
            logger.warning("LLM call failed — using offline fallback.")
            fallback = tools.simplify_text(deps=deps, text=prompt)
            if on_chunk:
                on_chunk(fallback)
            return fallback

        # Collect the streaming response — either tool calls or text content.
        collected_content = ""
        tool_calls: dict[int, dict[str, Any]] = {}

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                collected_content += delta.content
                if on_chunk:
                    on_chunk(delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": "",
                        }
                    if tc.function.arguments:
                        tool_calls[idx]["arguments"] += tc.function.arguments

        # No tool calls means we have a final answer.
        if not tool_calls:
            return collected_content

        # Feed tool results back into the conversation.
        messages.append(
            {
                "role": "assistant",
                "content": collected_content or None,
                "tool_calls": [
                    {
                        "id": call["id"],
                        "type": "function",
                        "function": {
                            "name": call["name"],
                            "arguments": call["arguments"],
                        },
                    }
                    for call in tool_calls.values()
                ],
            }
        )

        for call in tool_calls.values():
            try:
                args = json.loads(call["arguments"])
            except json.JSONDecodeError:
                args = {}
            output = _run_tool(call["name"], args, deps)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": output,
                }
            )

    # Reached the iteration limit without a final text reply.
    return (
        "I wasn't able to complete that request.\n\n"
        "Nothing has been lost. Here's what you can try:\n"
        "- Rephrase your request and try again\n"
        "- Break it into a smaller piece — for example, paste just the message you want simplified\n"
        "- DM Clarion directly if you'd prefer a quieter conversation"
    )
