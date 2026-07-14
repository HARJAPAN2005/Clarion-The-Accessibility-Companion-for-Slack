"""
Clarion — HTTP + OAuth entry point.

Run this instead of app.py when you want Clarion to use the **Slack MCP Server**
(required to read thread history for catch-up digests via MCP rather than raw
Web API calls). This mirrors the Slack Agent Kit `app_oauth.py` pattern.

    ngrok http 3000
    # set socket_mode_enabled=false in manifest.json and point redirect_urls at ngrok
    slack run app_oauth.py

Then open the install URL printed in the terminal to install Clarion via OAuth.
"""

import logging
import os

from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from listeners import register_listeners

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clarion")

oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    scopes=[
        "app_mentions:read",
        "assistant:write",
        "channels:history",
        "channels:read",
        "chat:write",
        "files:read",
        "groups:history",
        "groups:read",
        "im:history",
        "im:read",
        "im:write",
        "metadata.message:read",
        "reactions:read",
        "reactions:write",
        "users:read",
    ],
    redirect_uri=os.environ.get("SLACK_REDIRECT_URI"),
    installation_store=FileInstallationStore(base_dir="./data/installations"),
    state_store=FileOAuthStateStore(expiration_seconds=600, base_dir="./data/states"),
)

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    oauth_settings=oauth_settings,
)

register_listeners(app)


if __name__ == "__main__":
    logger.info("⚓ Clarion (HTTP/OAuth + Slack MCP Server) starting on :3000")
    app.start(port=int(os.environ.get("PORT", 3000)))
