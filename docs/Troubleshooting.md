# Troubleshooting

This document covers common issues and how to resolve them.

---

## Clarion does not respond in Slack

**Checklist:**

1. Is Clarion running? Check your terminal for `"Clarion is online"`.
2. Is `SLACK_BOT_TOKEN` correct? It must start with `xoxb-`.
3. Is `SLACK_APP_TOKEN` correct? It must start with `xapp-`.
4. Does Clarion have access to the channel? In Socket Mode, Clarion only
   responds to channels it has been invited to.
5. Check your Slack app's **Event Subscriptions** — `app_mention`, `message.im`,
   `message.channels`, and `message.groups` must all be enabled.

---

## Clarion responds with offline fallback text

You will see responses like "✨ *Clarion made this easier to read*" with only
mechanical jargon replacement (no real AI rewriting). This means:

- `OPENROUTER_API_KEY` is not set, or
- The OpenRouter API is unreachable, or
- All retry attempts failed.

**Fix:**
```bash
# Verify the key is set
echo $OPENROUTER_API_KEY

# Test reachability
curl -s https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | head -c 200
```

---

## Image descriptions don't work

1. Is `GEMINI_API_KEY` set? Check with `echo $GEMINI_API_KEY`.
2. Is `OPENROUTER_VISION_MODEL` set if Gemini is not configured?
3. Does the bot have `files:read` scope? Check in your Slack app settings
   under **OAuth & Permissions**.
4. Is the image a file upload (not a URL link)? The shortcut only works on
   uploaded files.

---

## Thread summaries return "Nothing to summarize"

1. Is the thread in a channel Clarion has been invited to?
2. Does the thread have replies? The shortcut must be used on a message that
   already has thread replies, not the first message.
3. Check the logs for `conversations.replies failed` — this indicates a
   missing `channels:history` or `groups:history` scope.

---

## `slack run` fails with an import error

```
ModuleNotFoundError: No module named 'slack_bolt'
```

Your virtual environment is not activated, or dependencies are not installed.

```bash
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

---

## `SLACK_CLIENT_ID environment variable is not defined`

You are running `app.py` but have `SLACK_CLIENT_ID` missing. This error only
appears if you accidentally ran `app_oauth.py` instead of `app.py`.

For Socket Mode development, always run:
```bash
python app.py
```

---

## Rate limit errors (429)

Clarion has built-in exponential backoff for rate limit errors (up to 2
retries with 1s and 2s delays). If you see persistent rate limiting:

- You may be on a free OpenRouter tier with strict rate limits.
- Switch to a model with higher rate limits, or add `OPENROUTER_MODEL` to
  a paid tier model.

---

## The App Home is blank

The App Home requires the `app_home_opened` event to be enabled. Verify in
your Slack app settings under **Event Subscriptions → Bot Events** that
`app_home_opened` is listed.

---

## Logging

Clarion uses Python's standard `logging` module. Increase verbosity by setting
the log level:

```python
# In app.py, change:
logging.basicConfig(level=logging.DEBUG, ...)
```

Or set the environment variable:
```bash
PYTHONLOGGER=DEBUG python app.py
```

Key logger names:
- `clarion` — main app lifecycle
- `clarion.agent` — agent loop and LLM calls
- `clarion.tools` — tool execution
- `clarion.config` — client initialisation
- `clarion.stream` — Bolt streaming surface
- `clarion.mcp` — Slack MCP Server calls
- `clarion.rts` — Real-Time Search calls
