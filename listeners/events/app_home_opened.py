from logging import Logger

from slack_bolt import BoltContext
from slack_sdk import WebClient

from listeners.views.home import build_home_view

SUGGESTED_PROMPTS = [
    {
        "title": "✨ Make this easier to read",
        "message": "Simplify this: Per my last, let's circle back to operationalize the synergies by EOD.",
    },
    {
        "title": "📌 Catch me up on this thread",
        "message": "Catch me up on the conversation I'm in.",
    },
    {
        "title": "💡 Help me understand this term",
        "message": "What does OKR mean in this workspace?",
    },
    {
        "title": "🌍 Is this clear for everyone?",
        "message": "Is this clear for everyone? 'We need to leverage our bandwidth to move the needle ASAP.'",
    },
]


def handle_app_home_opened(
    client: WebClient, event: dict, context: BoltContext, logger: Logger
) -> None:
    """agent_view: fires for both Home and Messages tabs — branch on event['tab']."""
    try:
        user_id = event.get("user") or context.user_id
        if event.get("tab") == "messages":
            client.assistant_threads_setSuggestedPrompts(
                channel_id=event["channel"],
                title="What can Clarion help you with?",
                prompts=SUGGESTED_PROMPTS,
            )
            return

        # Home tab: accessibility preferences dashboard.
        client.views_publish(user_id=user_id, view=build_home_view(user_id))
    except Exception as e:
        logger.exception(f"Failed to handle app_home_opened: {e}")
