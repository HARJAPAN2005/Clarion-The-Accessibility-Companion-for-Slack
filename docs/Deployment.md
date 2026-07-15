# Deployment Guide

This guide covers all supported deployment modes for Clarion.

---

## Mode 1 — Socket Mode (Recommended for development)

Socket Mode connects Clarion to Slack over a persistent WebSocket. No
public-facing URL is required. This is the easiest way to run Clarion locally.

### Prerequisites

- Python 3.10+
- A Slack app with Socket Mode enabled (see [DeveloperGuide.md](DeveloperGuide.md))
- `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` in your `.env`

### Start

```bash
cp .env.example .env
# Fill in SLACK_BOT_TOKEN and SLACK_APP_TOKEN
python app.py
# or: make dev
```

---

## Mode 2 — HTTP + OAuth (Production, enables Slack MCP Server)

HTTP + OAuth mode runs Clarion as a standard web server. This is required for:
- The Slack MCP Server (governed thread history access)
- Multi-workspace installations
- Production deployments

### Prerequisites

- A public HTTPS URL (use ngrok for local testing)
- All Slack OAuth credentials in `.env`

### Setup with ngrok (local testing)

```bash
# Start a tunnel
ngrok http 3000

# Copy the HTTPS URL (e.g. https://abc123.ngrok-free.app)
# Set it in .env:
SLACK_REDIRECT_URI=https://abc123.ngrok-free.app/slack/oauth_redirect
```

Update `manifest.json`:
```json
{
  "settings": {
    "socket_mode_enabled": false
  },
  "oauth_config": {
    "redirect_urls": ["https://abc123.ngrok-free.app/slack/oauth_redirect"]
  }
}
```

In your Slack app settings, enable **Agents → Model Context Protocol**.

```bash
# Fill in .env with SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SLACK_SIGNING_SECRET
SLACK_MCP_ENABLED=true

# Start the HTTP server
python app_oauth.py
```

Visit the install URL printed in the terminal to install via OAuth.

---

## Mode 3 — Docker (Socket Mode)

```bash
# Build the image
docker build -t clarion:latest .

# Run with your .env file
docker run --rm --env-file .env clarion:latest
```

### Docker Compose

```bash
# Start with Docker Compose
docker compose up

# Stop
docker compose down
```

Docker Compose automatically mounts the `.env` file and persists OAuth
installation data in a named volume (`clarion_data`).

---

## Mode 4 — Docker (HTTP + OAuth)

```bash
docker compose run --rm clarion python app_oauth.py
```

Or override the command in `docker-compose.yml`:

```yaml
services:
  clarion:
    command: python app_oauth.py
```

---

## Cloud Deployment

### Fly.io

```bash
fly launch --name clarion --region sin
fly secrets import < .env
fly deploy
```

### Railway

1. Connect your GitHub repository to Railway.
2. Set environment variables in the Railway dashboard.
3. Railway detects the `Dockerfile` and deploys automatically.

### Heroku

```bash
heroku create clarion-app
heroku config:set $(cat .env | grep -v '^#' | xargs)
git push heroku main
```

### Google Cloud Run

```bash
gcloud run deploy clarion \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="$(cat .env | grep -v '^#' | tr '\n' ',')"
```

---

## Environment Variables Reference

See [.env.example](../.env.example) for the complete list with descriptions.

### Required for all modes

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | Bot user OAuth token (xoxb-...) |
| `SLACK_APP_TOKEN` | App-level token (Socket Mode only, xapp-...) |

### Required for AI features

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `GEMINI_API_KEY` | Google Gemini API key (vision) |

### Required for HTTP + OAuth mode

| Variable | Description |
|---|---|
| `SLACK_CLIENT_ID` | OAuth client ID |
| `SLACK_CLIENT_SECRET` | OAuth client secret |
| `SLACK_SIGNING_SECRET` | Request signing secret |
| `SLACK_REDIRECT_URI` | OAuth redirect URL |
| `SLACK_MCP_ENABLED` | Set to `"true"` |

---

## Health Check

The Docker health check runs:
```bash
python -c "import app"
```

This verifies that the Python environment and all imports are healthy.

For production monitoring, consider adding a dedicated `/health` endpoint to
`app_oauth.py` using Bolt's built-in HTTP handling.
