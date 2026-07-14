from logging import Logger

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from agent import ClarionDeps, run_clarion
from thread_context import pref_store, session_store
from listeners._stream import stream_reply


def handle_message(
    client: WebClient,
    context: BoltContext,
    event: dict,
    logger: Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
) -> None:
    """Handle DMs to Clarion and follow-ups in threads it's engaged in."""
    subtype = event.get("subtype")
    if subtype and subtype != "file_share":
        return
    if event.get("bot_id"):
        return

    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None
    channel_id = context.channel_id
    thread_ts = event.get("thread_ts") or event["ts"]

    if is_dm:
        pass
    elif is_thread_reply:
        # Only continue in channel threads Clarion has already joined.
        if session_store.get_session(channel_id, event["thread_ts"]) is None:
            return
    else:
        return  # top-level channel messages are handled by app_mention

    try:
        text = event.get("text", "").strip()
        files = event.get("files", [])
        
        for f in files:
            url = f.get("url_private") or f.get("permalink", "")
            if url:
                text += f"\n\n[Attached image: {url}]"
                
        if not text.strip():
            return
        user_id = context.user_id

        if is_dm and session_store.get_session(channel_id, thread_ts) is None:
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

        stream_reply(
            say,
            say_stream,
            runner=lambda on_chunk: run_clarion(text, deps, on_chunk=on_chunk),
            thread_ts=thread_ts,
        )
        session_store.start_session(channel_id, thread_ts, f"s-{event['ts']}")
        logger.info("message handled (dm=%s) in %s", is_dm, channel_id)

    except Exception as e:
        logger.exception(f"Failed to handle message: {e}")
