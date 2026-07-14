import re
from logging import Logger

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from agent import ClarionDeps, run_clarion
from thread_context import pref_store, session_store
from listeners._stream import stream_reply
from listeners.views.feedback_builder import build_feedback_blocks


def handle_app_mentioned(
    client: WebClient,
    context: BoltContext,
    event: dict,
    logger: Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
) -> None:
    """Handle @Clarion mentions in channels."""
    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        files = event.get("files", [])
        
        for f in files:
            url = f.get("url_private") or f.get("permalink", "")
            if url:
                text += f"\n\n[Attached image: {url}]"
                
        thread_ts = event.get("thread_ts") or event["ts"]
        user_id = context.user_id

        cleaned = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
        if not cleaned:
            say(
                text=(
                    "Hi 👋 I'm Clarion — the accessibility layer for Slack.\n\n"
                    "I make conversations clearer and easier to follow for everyone, "
                    "without changing how your team works.\n\n"
                    "*Here's what I can do:*\n"
                    "• *Simplify a message* — paste any text or use the `···` shortcut\n"
                    "• *Catch you up on a thread* — `@Clarion catch me up`\n"
                    "• *Explain a term* — `@Clarion what does OKR mean in this channel?`\n"
                    "• *Check a draft* — `@Clarion is this clear for everyone: <your message>`\n"
                    "• *Describe an image* — use the Describe image shortcut\n\n"
                    "_Every response is designed to be readable by everyone — "
                    "including people using screen readers, non-native speakers, "
                    "and anyone who reads differently._"
                ),
                thread_ts=thread_ts,
            )
            return

        # 👀 only on the first (non-threaded) mention.
        if not event.get("thread_ts"):
            client.reactions_add(channel=channel_id, timestamp=event["ts"], name="eyes")

        set_status(
            status="🧠 Understanding your request…",
            loading_messages=[
                "🔍 Reading the conversation…",
                "📝 Preparing a clearer version…",
                "✨ Making it easier to understand…",
                "✅ Almost ready…",
            ],
        )

        deps = ClarionDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            prefs=pref_store.get(user_id) if user_id else {},
        )

        # If they mentioned Clarion inside a thread, give it that context.
        prompt = cleaned
        if event.get("thread_ts"):
            prompt = f"(In an existing thread channel_id={channel_id} thread_ts={thread_ts}) {cleaned}"

        stream_reply(
            say,
            say_stream,
            runner=lambda on_chunk: run_clarion(prompt, deps, on_chunk=on_chunk),
            thread_ts=thread_ts,
        )

        # Feedback + mark resolved affordance.
        say(blocks=build_feedback_blocks(), text="Was this clearer?", thread_ts=thread_ts)
        session_store.start_session(channel_id, thread_ts, f"s-{event['ts']}")
        client.reactions_add(channel=channel_id, timestamp=event["ts"], name="white_check_mark")
        logger.info("app_mention handled in %s", channel_id)

    except Exception as e:
        logger.exception(f"Failed to handle app_mention: {e}")
        try:
            say(
                text=(
                    "⚠️ *I wasn't able to complete that request.*\n\n"
                    "Nothing has been lost. Here's what you can try:\n"
                    "• Rephrase your request and mention me again\n"
                    "• DM me directly — sometimes a quieter one-on-one works better\n"
                    "• Use the message shortcut from the `···` menu"
                ),
                thread_ts=thread_ts,
            )
        except Exception:
            pass
