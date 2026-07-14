from logging import Logger

from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient

from thread_context import pref_store
from listeners.views.home import build_home_view


def _handle_feedback(ack: Ack, body: dict, logger: Logger) -> None:
    ack()
    value = body["actions"][0]["value"]
    logger.info("feedback=%s user=%s", value, body.get("user", {}).get("id"))


def _set_reading_level(ack: Ack, body: dict, client: WebClient, context: BoltContext) -> None:
    ack()
    user_id = context.user_id
    level = body["actions"][0]["selected_option"]["value"]
    pref_store.set(user_id, reading_level=level)
    client.views_publish(user_id=user_id, view=build_home_view(user_id))


def _set_language(ack: Ack, body: dict, client: WebClient, context: BoltContext) -> None:
    ack()
    user_id = context.user_id
    lang = body["actions"][0]["selected_option"]["value"]
    pref_store.set(user_id, language=None if lang == "Off" else lang)
    client.views_publish(user_id=user_id, view=build_home_view(user_id))


def _toggle_auto_alt(ack: Ack, body: dict, client: WebClient, context: BoltContext) -> None:
    ack()
    user_id = context.user_id
    current = pref_store.get(user_id).get("auto_alt_text", True)
    pref_store.set(user_id, auto_alt_text=not current)
    client.views_publish(user_id=user_id, view=build_home_view(user_id))


def register(app) -> None:
    app.action("feedback_clear")(_handle_feedback)
    app.action("feedback_unclear")(_handle_feedback)
    app.action("set_reading_level")(_set_reading_level)
    app.action("set_language")(_set_language)
    app.action("toggle_auto_alt")(_toggle_auto_alt)
