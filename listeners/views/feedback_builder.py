from typing import Any


def build_feedback_blocks() -> list[dict[str, Any]]:
    return [
        {
            "type": "actions",
            "block_id": "clarion_feedback",
            "elements": [
                {
                    "type": "button",
                    "action_id": "feedback_clear",
                    "text": {"type": "plain_text", "text": "Yes, clearer 👍"},
                    "style": "primary",
                    "value": "clear",
                },
                {
                    "type": "button",
                    "action_id": "feedback_unclear",
                    "text": {"type": "plain_text", "text": "Still unclear 👎"},
                    "value": "unclear",
                },
            ],
        }
    ]
