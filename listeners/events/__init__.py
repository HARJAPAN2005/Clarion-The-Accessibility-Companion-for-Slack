from slack_bolt import App

from listeners.events.app_home_opened import handle_app_home_opened
from listeners.events.app_mentioned import handle_app_mentioned
from listeners.events.message import handle_message


def register(app: App) -> None:
    app.event("app_mention")(handle_app_mentioned)
    app.event("message")(handle_message)
    app.event("app_home_opened")(handle_app_home_opened)
