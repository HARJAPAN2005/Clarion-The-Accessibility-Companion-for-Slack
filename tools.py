"""
Clarion accessibility tools.

Each function is callable directly (for shortcuts) and via the agent loop in
agent.py. Every tool degrades gracefully: if there's no OpenRouter key it returns
a deterministic, still-useful result so the sandbox demo never dead-ends.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from rts_client import realtime_search
from slack_mcp import fetch_thread_messages

logger = logging.getLogger("clarion.tools")

DEFAULT_MODEL = "poolside/laguna-xs-2.1:free"


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
            logger.info("[AI] Provider: OpenRouter")
        except ImportError:
            logger.error("openai package missing; run `pip install openai`.")
            return None
    return _openai_client


_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    if _gemini_client is None:
        try:
            from openai import OpenAI
            _gemini_client = OpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
        except ImportError:
            return None
    return _gemini_client


def _llm(system: str, user: str, image_url: str | None = None) -> str | None:
    """Single LLM call with robust error handling, retries, and offline fallback. Returns None if unavailable."""
    import time
    from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError
    
    if image_url:
        gemini_client = _get_gemini_client()
        if gemini_client:
            client = gemini_client
            configured_model = "gemini-3.5-flash"
        else:
            client = _get_openai_client()
            if not client:
                return None
            configured_model = os.getenv("OPENROUTER_VISION_MODEL")
            if not configured_model:
                return "The currently configured AI model does not support image understanding. Please configure a vision-capable OpenRouter model or provide a GEMINI_API_KEY."
    else:
        client = _get_openai_client()
        if not client:
            return None
        configured_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    content: list[dict[str, Any]] = [{"type": "text", "text": user}]
    if image_url:
        content.insert(0, {"type": "image_url", "image_url": {"url": image_url}})

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": content}
    ]

    def _attempt_call(model_to_use: str, retries: int = 0) -> str | None:
        for attempt in range(retries + 1):
            try:
                resp = client.chat.completions.create(
                    model=model_to_use,
                    max_tokens=1400,
                    temperature=0.2,
                    stream=False,
                    messages=messages
                )
                return resp.choices[0].message.content.strip()
            except RateLimitError as e:
                logger.warning(f"Rate limited (429). Attempt {attempt + 1}/{retries + 1}. Error: {e}")
                if attempt < retries:
                    time.sleep(2 ** attempt)  # 1s, 2s backoff
                    continue
                return None
            except APIError as e:
                status_code = getattr(e, 'status_code', None)
                if status_code == 404:
                    logger.error(f"Model unavailable (404): {model_to_use}")
                    raise e  # Let the outer block handle 404 fallback
                
                # Handle other known OpenRouter error codes
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
                logger.error(f"Unexpected error during LLM call: {e}")
                return None
        return None

    # First try the configured model
    try:
        result = _attempt_call(configured_model, retries=2)
        if result:
            return result
    except APIError as e:
        status_code = getattr(e, 'status_code', None)
        if status_code == 404 and configured_model != DEFAULT_MODEL:
            logger.info(f"Attempting fallback to default model: {DEFAULT_MODEL}")
            try:
                result = _attempt_call(DEFAULT_MODEL, retries=0)
                if result:
                    return result
            except Exception as inner_e:
                logger.error(f"Default model fallback failed: {inner_e}")

    logger.warning("[AI] Provider: Offline Fallback")
    return None


# ---------------------------------------------------------------------------
# Tool 1 — plain-language rewrite  (Slack AI capability)
# ---------------------------------------------------------------------------
_LEVELS = {
    "grade5": "a 10-year-old reading for the first time",
    "grade8": "a 13-year-old, using simple sentences",
    "plain": "a busy adult who reads quickly",
    "concise": "someone who needs only the critical essentials",
}

_SIMPLIFY_SYSTEM = """You are Clarion, an accessibility companion that makes workplace messages easier to understand.
Rewrite the message below so {audience} understands it immediately.

RULES — follow every one without exception:
1. Preserve ALL of these exactly: names, owners, dates, deadlines, priorities, action items, numbers.
2. Replace every piece of corporate jargon: "circle back" → "follow up", "leverage" → "use", "synergy" → "working together", "bandwidth" → "time/capacity", "move the needle" → "make progress", "low-hanging fruit" → "easy win", "touch base" → "check in", "action this" → "do this", "deep dive" → "look closely at", "best practice" → "what works well", "operationalize" → "put into action", "ideate" → "brainstorm", "align" → "agree", "deliverable" → "output/result".
3. Use short sentences. One idea per sentence. No walls of text.
4. Keep a professional, calm tone. Not casual. Not chatty.
5. Do NOT add intros like "Sure!" or "Here is the rewrite". Output only the rewritten message.
6. If language={language}, write the output in {language}.

Begin your reply with exactly this line (no variations):
✨ *Clarion made this easier to read* — every important detail is preserved.

Then the rewritten message on the next line.
Close with exactly this line on its own line:
_Clarity preserved. Complexity removed._"""


def simplify_text(
    deps: Any = None,
    text: str = "",
    reading_level: str = "plain",
    language: str | None = None,
    **_: Any,
) -> str:
    audience = _LEVELS.get(reading_level, _LEVELS["plain"])
    lang_note = language or "English"
    system = _SIMPLIFY_SYSTEM.format(audience=audience, language=lang_note)
    out = _llm(system, text)
    if out:
        return out
    return _mechanical_simplify(text)


def _mechanical_simplify(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    lines = []
    replacements = [
        (r"\b(leverage|utilize)\b", "use"),
        (r"\b(synergize|synergies|synergy)\b", "work together"),
        (r"\b(operationalize)\b", "put into action"),
        (r"\b(circle back|touch base)\b", "follow up"),
        (r"\b(bandwidth)\b", "capacity"),
        (r"\b(move the needle)\b", "make progress"),
        (r"\b(low.hanging fruit)\b", "easy win"),
        (r"\b(deep dive)\b", "detailed look"),
        (r"\b(ideate)\b", "brainstorm"),
        (r"\b(deliverable)\b", "output"),
        (r"\b(best practice)\b", "what works well"),
    ]
    for s in sentences:
        for pattern, repl in replacements:
            s = re.sub(pattern, repl, s, flags=re.I)
        if s.strip():
            lines.append(s.strip())
    body = "  ".join(lines) if lines else "(nothing to simplify)"
    return (
        "✨ *Clarion made this easier to read* — every important detail is preserved.\n"
        f"{body}\n\n"
        "_Clarity preserved. Complexity removed._"
    )


# ---------------------------------------------------------------------------
# Tool 2 — catch-up digest  (uses Slack MCP Server to read thread history)
# ---------------------------------------------------------------------------
_DIGEST_SYSTEM = """You are Clarion, an accessibility companion helping someone catch up on a conversation they missed.
Produce a structured, plain-language digest for someone returning from leave or joining a thread late.

RULES:
1. Extract all names, dates, deadlines, and responsibilities. Never skip them.
2. Identify who owns each action item by name.
3. Surface any blockers, risks, or unresolved items.
4. Sort action items by urgency — most urgent first.
5. Maximum 250 words total.
6. Never write one long paragraph. Always use the exact structure below.
7. If a section has nothing to report, write "None" — never omit the section header.
8. Sound like a supportive teammate, not a machine generating a report.

Output EXACTLY this structure:

📌 *You're all caught up. Here's what matters most.*
One to three calm, clear sentences on what this conversation is about and where things stand right now.

✅ *Decisions made*
- List each decision clearly. If none, write "None."

👤 *Who needs to do what*
- [Name] — what they need to do (by when, if mentioned)

📅 *Key dates and deadlines*
- List every date or deadline mentioned. If none, write "None."

❓ *Still being worked out*
- List anything unresolved or awaiting a decision.

Do not add any text outside this structure. Do not include a closing sentence."""


def summarize_thread(
    deps: Any = None,
    channel_id: str = "",
    thread_ts: str = "",
    **_: Any,
) -> str:
    client = getattr(deps, "client", None)
    messages = fetch_thread_messages(client, channel_id, thread_ts)
    if not messages:
        return (
            "📌 *Nothing to summarize yet.*\n\n"
            "When this conversation gets going, Clarion will help make it easy to follow.\n\n"
            "_Tip: use the shortcut from a message that already has replies._"
        )
    transcript = "\n".join(f"{m['user']}: {m['text']}" for m in messages)
    out = _llm(_DIGEST_SYSTEM, transcript)
    if out:
        return out
    # Offline fallback: structured skeleton
    last = messages[-1]["text"][:140]
    return (
        f"📌 *You're all caught up. Here's what matters most.*\nThis conversation has {len(messages)} messages.\n\n"
        f"✅ *Decisions made*\n{last}\n\n"
        "👤 *Who needs to do what*\nSee the thread for the full picture.\n\n"
        "📅 *Key dates and deadlines*\nNone detected — check the thread directly.\n\n"
        "❓ *Still being worked out*\nReview the full thread for anything unresolved."
    )


# ---------------------------------------------------------------------------
# Tool 3 — screen-reader alt-text
# ---------------------------------------------------------------------------
_ALT_SYSTEM = """You are Clarion, an accessibility companion creating descriptions for blind, low-vision, and screen-reader users.

RULES:
1. First: one tight sentence under 125 characters — this is the alt attribute text. Do NOT start with "Image of" or "Photo of".
2. Then: a thorough description covering layout, objects, colours, text (if any), relationships between elements, and why it matters in context.
3. If the image contains any text, transcribe it word for word inside the description.
4. Never invent details you cannot see. If something is unclear, say so plainly.
5. Write as if speaking to a colleague who cannot see the screen at all.

Output this exact format:

🖼 *Screen-reader friendly description*
[one concise alt-text sentence under 125 characters]

🔍 *Full visual description*
[thorough paragraph — layout, content, text transcription if present, context]

If the image contained text, end with: _All text in this image has been transcribed above._"""


def _download_slack_image_as_base64(url: str, token: str) -> str | None:
    import requests
    import base64
    if not url.startswith("http"):
        return None
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if resp.status_code != 200:
            return None
        mime = resp.headers.get("Content-Type", "image/jpeg")
        b64 = base64.b64encode(resp.content).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        logger.error(f"Failed to download image: {e}")
        return None

def generate_alt_text(
    deps: Any = None,
    image_url: str = "",
    context: str = "",
    **_: Any,
) -> str:
    if image_url.startswith("http"):
        token = getattr(deps, "client", None).token if getattr(deps, "client", None) else os.environ.get("SLACK_BOT_TOKEN")
        if token:
            b64_url = _download_slack_image_as_base64(image_url, token)
            if b64_url:
                image_url = b64_url

    user = (
        f"Message context: {context}\n\nDescribe this image for someone who cannot see it."
        if context
        else "Describe this image for someone who cannot see it."
    )
    out = _llm(_ALT_SYSTEM, user, image_url=image_url)
    if out:
        return out
    return (
        "🖼 *Screen-reader friendly description*\n"
        "Clarion needs an active connection to describe this image.\n\n"
        "🔍 *Full visual description*\n"
        "_To make this image accessible to everyone, ask the person who shared it to add a "
        "brief description in the message. Good alt-text says what is shown and why it matters._"
    )


# ---------------------------------------------------------------------------
# Tool 4 — define term  (Real-Time Search API)
# ---------------------------------------------------------------------------
_DEFINE_SYSTEM = """You are Clarion, an accessibility companion helping someone understand a term they've encountered at work.
Write for someone who genuinely doesn't know this term and may feel uncertain about asking.
Make them feel informed and included — never embarrassed.

RULES:
1. Check the workspace search context first — it shows how THIS specific team uses the term.
2. Write in plain, everyday language. No assumed knowledge.
3. Be warm and direct. This is a helpful explanation between teammates.
4. Always include all three sections exactly as shown.

Output EXACTLY this structure:

💡 *Here's what that means*
[What it means in plain language — 1 to 3 short sentences. Make the person feel immediately informed.]

📍 *How your team uses it*
[Based on the workspace context, or the closest reasonable meaning if no context is available]

📝 *Example in a sentence*
[A concrete, realistic workplace sentence showing it in use]"""


def define_term(
    deps: Any = None,
    term: str = "",
    channel_id: str = "",
    **_: Any,
) -> str:
    hits = realtime_search(query=term, channel_id=channel_id)
    context_block = (
        "\n".join(f"- {h['snippet']} (source: {h['source']})" for h in hits)
        if hits
        else "No live workspace results found for this term."
    )
    user = f"Term: {term}\n\nLive workspace context:\n{context_block}"
    out = _llm(_DEFINE_SYSTEM, user)
    if out:
        return out
    if hits:
        return (
            f"💡 *Here's what that means*\n"
            f"Here's how your workspace uses *{term}*:\n{context_block}\n\n"
            f"_Everyone deserves conversations that are easy to understand._"
        )
    return (
        f"💡 *Here's what that means*\n"
        f"Clarion couldn't find a live definition for *{term}* — it may be shorthand unique to your team.\n\n"
        f"📍 *How your team uses it*\n"
        f"The best person to ask is whoever used this term in the conversation.\n\n"
        f"📝 *Example in a sentence*\n"
        f"Not available — a quick ask in the thread will get you the right answer."
    )


# ---------------------------------------------------------------------------
# Tool 5 — inclusive language check
# ---------------------------------------------------------------------------
_FLAGS = {
    r"\blow.hanging fruit\b": "easy win",
    r"\bboil the ocean\b": "take on too much at once",
    r"\bmove the needle\b": "make progress",
    r"\bping me\b": "message me",
    r"\bEOD\b": "end of day",
    r"\bASAP\b": "as soon as you can",
    r"\bWFH\b": "working from home",
    r"\bTL;?DR\b": "in short",
    r"\bleverage\b": "use",
    r"\bbandwidth\b": "capacity",
    r"\bsynerg\w+\b": "working together",
    r"\btouch base\b": "check in",
    r"\bcircle back\b": "follow up",
}

_INCLUSIVE_SYSTEM = """You are Clarion, an accessibility companion helping people communicate more clearly and inclusively.
Review the draft below as a supportive writing coach — not a critic. The goal is to help this message reach more people.

The people who benefit most from clearer writing: non-native speakers, people with dyslexia or ADHD, newcomers, screen-reader users, and anyone reading quickly under pressure.

RULES:
1. Only flag genuine barriers. Don't invent issues that aren't there.
2. Explain WHY each phrase creates difficulty — be specific, not generic.
3. Rewrite the full sentence, not just the flagged word.
4. Keep the tone warm and coaching. The writer is trying to communicate well.
5. If the message is already clear and inclusive: celebrate that warmly in one sentence. No sections needed.

Begin with: 🌍 *Here's a version that's easier for more people to understand.*

When issues exist, output this structure for each one (repeat as needed):

⚠️ *"[flagged phrase]"*
[Why this phrase creates a barrier for specific readers — be concrete and specific]

🌍 *A version that works for everyone*
[The full improved sentence — not just the changed word]

👥 *Who this helps most*
[Name the people who benefit — e.g. "non-native speakers unfamiliar with this sports metaphor"]

---

Small wording changes make a big difference."""


def inclusive_check(deps: Any = None, text: str = "", **_: Any) -> str:
    out = _llm(_INCLUSIVE_SYSTEM, text)
    if out:
        return out
    # Mechanical offline fallback
    found = []
    for pattern, repl in _FLAGS.items():
        m = re.search(pattern, text, flags=re.I)
        if m:
            found.append(
                f"⚠️ *\"{m.group(0)}\"*\n"
                f"This phrase may be unclear to people who didn't grow up with it — including non-native speakers and new team members.\n\n"
                f"🌍 *A version that works for everyone*\nTry: _{repl}_ instead.\n\n"
                f"👥 *Who this helps most*\nNon-native speakers, newcomers, and anyone unfamiliar with this expression.\n\n---"
            )
    if not found:
        return "✅ This message is clear and inclusive — Clarion didn't find anything that could create barriers."
    header = "🌍 *Here's a version that's easier for more people to understand.*\n\n"
    return header + "\n".join(found)
