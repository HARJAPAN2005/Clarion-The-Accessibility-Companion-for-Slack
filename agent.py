"""
Clarion agent core.

This wraps an AI agent (originally Claude Agent SDK, now OpenRouter/OpenAI).
Clarion exposes a small set of accessibility tools and lets the model decide
which to call based on the user's request:

    • simplify_text      – plain-language rewrite (Slack AI capability)
    • summarize_thread   – catch-up digest of a long thread
    • generate_alt_text  – screen-reader description of an image
    • define_term        – live acronym/jargon lookup (Real-Time Search API)
    • inclusive_check    – flags exclusionary or jargon-heavy phrasing

The class is deliberately framework-thin so the same code path runs in the demo
with or without a live OPENROUTER_API_KEY (a deterministic offline fallback keeps
the sandbox demo reliable if the network is flaky).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()

import tools

logger = logging.getLogger("clarion.agent")

DEFAULT_MODEL = "poolside/laguna-xs-2.1:free"

SYSTEM_PROMPT = """You are Clarion — the accessibility layer for Slack.
Your purpose is to make every workplace conversation easier to understand for everyone: people with dyslexia, ADHD, or cognitive differences; non-native English speakers; people who are blind or have low vision; and anyone joining a conversation late.

Your personality: calm, warm, helpful, and professional. You are a thoughtful teammate, not a chatbot.

Core principles:
- Plain language always. Short sentences. Common words. One idea per sentence.
- Never drop meaning. Preserve every decision, owner, date, number, and action item exactly.
- Never be condescending. You remove communication barriers — you don't simplify people.
- When describing an image: be specific enough that someone who cannot see it gets the full picture.
- When defining a term: treat the person as intelligent, just unfamiliar. Never make them feel they should already know.
- When checking a draft: be a supportive coach, not a critic. The writer is trying to communicate well.
- Respect the user's saved reading level and language preferences when provided.
- Never start a response with 'Sure!', 'Of course!', 'Great question!', or 'Certainly!'.
- Never use jargon yourself. Clarion practises what it preaches.

Always choose the right tool. When someone pastes text without an explicit request, default to simplify_text.
Keep responses tight — this is a chat surface. Be useful, not verbose."""


# ---------------------------------------------------------------------------
# Tool schema advertised to the model (OpenAI format)
# ---------------------------------------------------------------------------
TOOL_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "simplify_text",
            "description": "Rewrite text into clear plain language at the requested reading level, preserving all meaning, decisions, owners, dates and action items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to simplify."},
                    "reading_level": {
                        "type": "string",
                        "enum": ["grade5", "grade8", "plain", "concise"],
                        "description": "Target reading level. Defaults to 'plain'.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional ISO language name to translate the plain-language version into.",
                    },
                },
                "required": ["text"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_thread",
            "description": "Produce a plain-language catch-up digest of a Slack thread: the decision, who owns what, deadlines, and open questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string"},
                    "thread_ts": {"type": "string"},
                },
                "required": ["channel_id", "thread_ts"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_alt_text",
            "description": "Generate concise, useful screen-reader alt-text for an image, plus a longer description if the image is complex (a chart, diagram, or screenshot).",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {"type": "string"},
                    "context": {"type": "string", "description": "Surrounding message text, if any."},
                },
                "required": ["image_url"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "define_term",
            "description": "Define an acronym or piece of jargon using live Real-Time Search over workspace context and the web. Use for internal shorthand newcomers may not know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "channel_id": {"type": "string", "description": "Channel where the term appeared, for workspace-scoped search."},
                },
                "required": ["term"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inclusive_check",
            "description": "Scan a draft message for jargon, idioms, unexplained acronyms, or exclusionary phrasing and suggest clearer alternatives before it is sent.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    },
]


@dataclass
class ClarionDeps:
    """Everything a tool call needs at run time."""

    client: Any  # slack_sdk WebClient
    user_id: str | None = None
    channel_id: str | None = None
    prefs: dict[str, Any] = field(default_factory=dict)


# Map tool names to their Python implementations in tools.py
TOOL_IMPLS: dict[str, Callable[..., str]] = {
    "simplify_text": tools.simplify_text,
    "summarize_thread": tools.summarize_thread,
    "generate_alt_text": tools.generate_alt_text,
    "define_term": tools.define_term,
    "inclusive_check": tools.inclusive_check,
}


def _run_tool(name: str, args: dict[str, Any], deps: ClarionDeps) -> str:
    impl = TOOL_IMPLS.get(name)
    if impl is None:
        return f"(unknown tool: {name})"
    logger.info("tool_call name=%s args=%s", name, list(args.keys()))
    return impl(deps=deps, **args)


# Shared OpenAI client instance to avoid repeated initialization
_openai_client = None

def _get_openai_client():
    global _openai_client
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
        
    if _openai_client is None:
        try:
            from openai import OpenAI
            _openai_client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            logger.error("openai package missing; run `pip install openai`.")
            return None
    return _openai_client


def run_clarion(prompt: str, deps: ClarionDeps, on_chunk: Callable[[str], None] | None = None) -> str:
    """
    Run one turn of the Clarion agent.

    `on_chunk` (optional) receives streamed text so Bolt's say_stream can push
    partial output into Slack as it's generated.
    """
    client = _get_openai_client()
    if not client:
        # Offline deterministic path keeps the demo alive without a key/network.
        logger.warning("[AI] Provider: Offline Fallback")
        result = tools.simplify_text(deps=deps, text=prompt)
        if on_chunk:
            on_chunk(result)
        return result

    logger.info("[AI] Provider: OpenRouter")
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    configured_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    
    # Agent loop: let the model call tools until it produces a final answer.
    for _ in range(6):
        import time
        from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError
        
        def _attempt_call(model_to_use: str, retries: int = 0):
            for attempt in range(retries + 1):
                try:
                    return client.chat.completions.create(
                        model=model_to_use,
                        max_tokens=1400,
                        temperature=0.25,
                        tools=TOOL_SCHEMA,
                        messages=messages,
                        stream=True
                    )
                except RateLimitError as e:
                    logger.warning(f"Rate limited (429). Attempt {attempt + 1}/{retries + 1}. Error: {e}")
                    if attempt < retries:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                except APIError as e:
                    status_code = getattr(e, 'status_code', None)
                    if status_code == 404:
                        logger.error(f"Model unavailable (404): {model_to_use}")
                        raise e
                    if status_code in [401, 403]:
                        logger.error(f"Authentication/Authorization error ({status_code}): {e}")
                        return None
                    if status_code in [408, 500, 502, 503, 504]:
                        logger.error(f"Server error ({status_code}): {e}")
                        if attempt < retries:
                            time.sleep(2 ** attempt)
                            continue
                        return None
                    logger.error(f"Unexpected API error: {e}")
                    return None
                except (APIConnectionError, APITimeoutError) as e:
                    logger.error(f"Connection/Timeout error: {e}")
                    if attempt < retries:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                except Exception as e:
                    logger.error(f"Unexpected error during streaming LLM call: {e}")
                    return None
            return None

        response = None
        try:
            response = _attempt_call(configured_model, retries=2)
        except APIError as e:
            status_code = getattr(e, 'status_code', None)
            if status_code == 404 and configured_model != DEFAULT_MODEL:
                logger.info(f"Attempting fallback to default model: {DEFAULT_MODEL}")
                try:
                    response = _attempt_call(DEFAULT_MODEL, retries=0)
                except Exception as inner_e:
                    logger.error(f"Default model fallback failed: {inner_e}")
                    response = None

        if not response:
            logger.warning("[AI] Provider: Offline Fallback")
            fallback = tools.simplify_text(deps=deps, text=prompt)
            if on_chunk:
                on_chunk(fallback)
            return fallback

        # We will collect the streaming response.
        # It could be tool calls or text content.
        collected_content = ""
        tool_calls = {}

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            
            # Text stream chunk
            if delta.content:
                collected_content += delta.content
                if on_chunk:
                    on_chunk(delta.content)
            
            # Tool calls stream chunk
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {"id": tc.id, "name": tc.function.name, "arguments": ""}
                    if tc.function.arguments:
                        tool_calls[idx]["arguments"] += tc.function.arguments

        # If it returned content and no tools, we are done.
        if not tool_calls:
            return collected_content

        # Handle tool calls
        messages.append({
            "role": "assistant",
            "content": collected_content if collected_content else None,
            "tool_calls": [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": call["arguments"]
                    }
                } for call in tool_calls.values()
            ]
        })
        
        for call in tool_calls.values():
            try:
                args = json.loads(call["arguments"])
            except json.JSONDecodeError:
                args = {}
            output = _run_tool(call["name"], args, deps)
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": output
            })

    return (
        "⚠️ *I wasn't able to complete that request.*\n\n"
        "Nothing has been lost. Here's what you can try:\n"
        "\u2022 Rephrase your request and try again\n"
        "\u2022 Break it into a smaller piece — for example, paste just the message you want simplified\n"
        "\u2022 DM Clarion directly if you'd prefer a quieter conversation"
    )
