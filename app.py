"""
app — Clarion Socket Mode entry point.

Start Clarion in Socket Mode for local development:

    python app.py

Or use the Slack CLI:

    slack run

For the HTTP + OAuth server (which enables the Slack MCP Server), run
``app_oauth.py`` instead.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from listeners import register_listeners

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clarion")

app = App(token=os.environ["SLACK_BOT_TOKEN"])
register_listeners(app)


def _startup_check() -> None:
    """Log environment and connectivity diagnostics at startup."""
    separator = "-" * 48
    logger.info(separator)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        logger.info("OpenRouter API key: configured")
    else:
        logger.warning("OpenRouter API key: not set — running in offline fallback mode")

    model = os.environ.get("OPENROUTER_MODEL", "poolside/laguna-xs-2.1:free")
    vision_model = os.environ.get("OPENROUTER_VISION_MODEL", "not configured")
    if os.environ.get("GEMINI_API_KEY"):
        vision_model = "gemini-2.0-flash (via Google Gemini API)"

    logger.info("Text model  : %s", model)
    logger.info("Vision model: %s", vision_model)

    if api_key:
        try:
            import requests

            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )
            if response.status_code == 200:
                logger.info("OpenRouter reachability: OK")
            else:
                logger.warning("OpenRouter reachability: HTTP %s", response.status_code)
        except Exception as exc:
            logger.warning("OpenRouter reachability: unreachable (%s)", exc)

    logger.info(separator)


def main() -> None:
    """Start the Clarion Socket Mode server."""
    _startup_check()
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    logger.info("Clarion is online — making Slack accessible to everyone.")
    handler.start()


if __name__ == "__main__":
    main()
