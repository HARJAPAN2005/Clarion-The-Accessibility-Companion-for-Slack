"""Register every Clarion listener with the Bolt app."""

from slack_bolt import App

from listeners import actions, events, shortcuts


def register_listeners(app: App) -> None:
    events.register(app)
    actions.register(app)
    shortcuts.register(app)
