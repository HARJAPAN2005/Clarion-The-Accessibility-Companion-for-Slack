from typing import Any

from thread_context import pref_store

_LEVEL_LABELS = {
    "grade5": "Simple — short sentences, everyday words",
    "grade8": "Clear — plain language, no jargon",
    "plain": "Natural — clear and easy to follow",
    "concise": "Concise — key points only",
}


def build_home_view(user_id: str) -> dict[str, Any]:
    prefs = pref_store.get(user_id)
    current_level = _LEVEL_LABELS.get(prefs["reading_level"], _LEVEL_LABELS["plain"])
    lang = prefs.get("language") or "Off"
    auto_alt = "On ✅" if prefs.get("auto_alt_text", True) else "Off"
    lang_display = f"{lang} ✅" if lang != "Off" else "Off"

    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "⚓  Clarion — The Accessibility Layer for Slack"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Welcome to Clarion.*\n"
                        "Your accessibility companion for Slack.\n\n"
                        "Whether you're catching up after time away, reading in another language, "
                        "using a screen reader, or simply trying to communicate more clearly — "
                        "Clarion is here to make every conversation easier to understand.\n\n"
                        "• Use the `···` shortcut on any message to simplify it\n"
                        "• Use *Catch me up* to get a plain-language digest of any thread\n"
                        "• Use *Describe image* to generate a screen-reader friendly description\n"
                        "• Mention `@Clarion` in any channel, or just DM me directly"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Your Preferences"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Reading Style*\n"
                        f"_Currently: {current_level}_\n"
                        "Choose how Clarion rewrites messages for you. "
                        "Simpler styles use shorter sentences and more common words."
                    ),
                },
                "accessory": {
                    "type": "static_select",
                    "action_id": "set_reading_level",
                    "placeholder": {"type": "plain_text", "text": "Choose a style"},
                    "options": [
                        {"text": {"type": "plain_text", "text": label}, "value": key}
                        for key, label in _LEVEL_LABELS.items()
                    ],
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Preferred Language*\n"
                        f"_Currently: {lang_display}_\n"
                        "Clarion can explain messages in the language you're most comfortable reading. "
                        "Useful for non-native speakers or multilingual teams."
                    ),
                },
                "accessory": {
                    "type": "static_select",
                    "action_id": "set_language",
                    "placeholder": {"type": "plain_text", "text": "Off"},
                    "options": [
                        {"text": {"type": "plain_text", "text": t}, "value": t}
                        for t in ["Off", "Spanish", "French", "Hindi", "Mandarin", "Arabic", "Portuguese"]
                    ],
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Automatically Describe Images*\n"
                        f"_Currently: {auto_alt}_\n"
                        "When turned on, Clarion generates screen-reader friendly descriptions "
                        "whenever images appear in your conversations."
                    ),
                },
                "accessory": {
                    "type": "button",
                    "action_id": "toggle_auto_alt",
                    "text": {"type": "plain_text", "text": "Toggle"},
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "Built for the Slack Agent Builder Challenge · "
                            "Powered by Slack AI, the Slack MCP Server & the Real-Time Search API"
                        ),
                    }
                ],
            },
        ],
    }
