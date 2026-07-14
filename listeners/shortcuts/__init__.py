from logging import Logger

from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient

import tools
from agent import ClarionDeps
from thread_context import pref_store


def _open_dm(client: WebClient, user_id: str) -> str:
    resp = client.conversations_open(users=user_id)
    return resp["channel"]["id"]


def _simplify_message(ack: Ack, shortcut: dict, client: WebClient, context: BoltContext, logger: Logger) -> None:
    """Message shortcut → rewrite the selected message in plain language."""
    ack()
    try:
        user_id = context.user_id
        message = shortcut["message"]
        text = message.get("text", "")
        prefs = pref_store.get(user_id)
        deps = ClarionDeps(client=client, user_id=user_id, channel_id=shortcut["channel"]["id"], prefs=prefs)
        result = tools.simplify_text(
            deps=deps, text=text,
            reading_level=prefs.get("reading_level", "plain"),
            language=prefs.get("language"),
        )
        dm = _open_dm(client, user_id)
        client.chat_postMessage(channel=dm, text=result)
    except Exception as e:
        logger.exception(f"simplify_message shortcut failed: {e}")
        try:
            dm = _open_dm(client, user_id)
            client.chat_postMessage(
                channel=dm,
                text=(
                    "⚠️ *I wasn't able to simplify that message.*\n\n"
                    "Nothing has been lost. Here's what you can try:\n"
                    "• DM me the text directly and I'll rewrite it for you\n"
                    "• Make sure the message contains readable text\n"
                    "• Try again in a moment"
                ),
            )
        except Exception:
            pass


def _alt_text_message(ack: Ack, shortcut: dict, client: WebClient, context: BoltContext, logger: Logger) -> None:
    """Message shortcut → generate screen-reader alt-text for images in the message."""
    ack()
    try:
        user_id = context.user_id
        message = shortcut["message"]
        files = message.get("files", [])
        deps = ClarionDeps(client=client, user_id=user_id, channel_id=shortcut["channel"]["id"])
        if not files:
            out = (
                "🖼️ *There are no images in that message.*\n\n"
                "_Tip: use the Describe image shortcut on a message that has an uploaded image attached._"
            )
        else:
            parts = []
            for f in files:
                url = f.get("url_private") or f.get("permalink", "")
                result = tools.generate_alt_text(deps=deps, image_url=url, context=message.get("text", ""))
                parts.append(result)
            out = "\n\n".join(parts)
        dm = _open_dm(client, user_id)
        client.chat_postMessage(channel=dm, text=out)
    except Exception as e:
        logger.exception(f"alt_text_message shortcut failed: {e}")
        try:
            dm = _open_dm(client, user_id)
            client.chat_postMessage(
                channel=dm,
                text=(
                    "⚠️ *I wasn't able to describe that image.*\n\n"
                    "Nothing has been lost. Here's what you can try:\n"
                    "• Make sure the image is a standard file upload, not a link\n"
                    "• Try again in a moment"
                ),
            )
        except Exception:
            pass


def _digest_thread(ack: Ack, shortcut: dict, client: WebClient, context: BoltContext, logger: Logger) -> None:
    """Message shortcut → catch-up digest of the selected message's thread."""
    ack()
    try:
        user_id = context.user_id
        message = shortcut["message"]
        channel_id = shortcut["channel"]["id"]
        thread_ts = message.get("thread_ts") or message.get("ts")
        deps = ClarionDeps(client=client, user_id=user_id, channel_id=channel_id)
        result = tools.summarize_thread(deps=deps, channel_id=channel_id, thread_ts=thread_ts)
        dm = _open_dm(client, user_id)
        client.chat_postMessage(channel=dm, text=result)
    except Exception as e:
        logger.exception(f"digest_thread shortcut failed: {e}")
        try:
            dm = _open_dm(client, user_id)
            client.chat_postMessage(
                channel=dm,
                text=(
                    "⚠️ *I wasn't able to summarize that thread.*\n\n"
                    "Nothing has been lost. Here's what you can try:\n"
                    "• Use the shortcut from a message that already has replies\n"
                    "• Make sure the thread is in a channel Clarion has access to\n"
                    "• Try again in a moment"
                ),
            )
        except Exception:
            pass


def register(app) -> None:
    app.shortcut("simplify_message")(_simplify_message)
    app.shortcut("alt_text_message")(_alt_text_message)
    app.shortcut("digest_thread")(_digest_thread)
