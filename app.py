"""
Clarion — the accessibility layer for Slack.

Socket Mode entry point. Use this for local development and the hackathon demo.
For the Slack MCP Server (HTTP + OAuth), run `app_oauth.py` instead.

    slack run                # runs this file (socket mode)
    slack run app_oauth.py   # runs the HTTP/OAuth server (enables the Slack MCP Server)
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from listeners import register_listeners

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clarion")

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Wire up every event, action, shortcut, and view handler.
register_listeners(app)


def _startup_check() -> None:
    print("-" * 36)
    
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        print("✓ API Key Found")
    else:
        print("✗ API Key Missing (falling back to offline mode)")
        
    model = os.environ.get("OPENROUTER_MODEL", "poolside/laguna-xs-2.1:free")
    vision_model = os.environ.get("OPENROUTER_VISION_MODEL", "Not configured")
    if os.environ.get("GEMINI_API_KEY"):
        vision_model = "gemini-3.5-flash (via Google API)"
    print(f"✓ Text Model Loaded: {model}")
    print(f"✓ Vision Model Loaded: {vision_model}")
    
    if api_key:
        try:
            import requests
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            if response.status_code == 200:
                print("✓ OpenRouter Reachable")
            else:
                print(f"✗ OpenRouter Unreachable (HTTP {response.status_code})")
        except Exception as e:
            print(f"✗ OpenRouter Unreachable: {e}")
            
    print("-" * 36)
    print("[AI] Provider    : OpenRouter")
    print(f"[AI] Text Model  : {model}")
    print(f"[AI] Vision Model: {vision_model}")
    print("-" * 36)


def main() -> None:
    _startup_check()
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    logger.info("⚓ Clarion is online — making Slack accessible to everyone.")
    handler.start()


if __name__ == "__main__":
    main()
