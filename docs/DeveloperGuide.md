# Developer Guide

This guide covers everything you need to set up a local development environment,
understand the project structure, and make contributions to Clarion.

---

## Prerequisites

- **Python 3.10 or higher** — Clarion uses `match` statements and union type
  syntax that require Python 3.10+.
- **A Slack workspace** — you need a workspace where you can install
  development apps.
- **A Slack app** — create one at [api.slack.com/apps](https://api.slack.com/apps).

---

## Local Setup

```bash
# 1. Clone your fork
git clone https://github.com/<your-username>/Clarion-The-Accessibility-Companion-for-Slack.git
cd Clarion-The-Accessibility-Companion-for-Slack

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate          # Windows

# 3. Install all dependencies including dev extras
pip install -e ".[dev]"
# or: make install

# 4. Copy the environment template and fill in your credentials
cp .env.example .env

# 5. Start Clarion
python app.py
# or: make dev
```

---

## Project Structure

```
clarion/
├── app.py                  # Socket Mode entry point
├── app_oauth.py            # HTTP + OAuth entry point
├── agent.py                # AI agent loop and tool dispatch
├── tools.py                # Five accessibility tool implementations
├── config.py               # Environment variables and AI client factories
├── thread_context.py       # In-memory session and preference stores
├── rts_client.py           # Real-Time Search API client
├── slack_mcp.py            # Slack MCP Server / Web API bridge
├── manifest.json           # Slack app manifest (scopes, shortcuts, events)
├── pyproject.toml          # Project config, deps, tool settings
├── requirements.txt        # Pinned runtime dependencies
├── Makefile                # Developer convenience targets
├── Dockerfile              # Multi-stage container build
├── docker-compose.yml      # Local Docker development
├── .env.example            # Environment variable template
├── .editorconfig           # Editor formatting rules
├── .devcontainer/          # VS Code dev container config
│
├── listeners/
│   ├── __init__.py         # Registers all listeners with the Bolt app
│   ├── _stream.py          # Defensive Bolt streaming helper
│   ├── events/
│   │   ├── __init__.py     # Event listener registration
│   │   ├── app_mentioned.py
│   │   ├── message.py
│   │   └── app_home_opened.py
│   ├── actions/
│   │   └── __init__.py     # Block Kit action handlers
│   ├── shortcuts/
│   │   └── __init__.py     # Message shortcut handlers
│   └── views/
│       ├── __init__.py
│       ├── home.py         # App Home Block Kit view builder
│       └── feedback_builder.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Shared pytest fixtures
│   ├── test_tools.py       # Offline tests for all 5 tools
│   ├── test_config.py      # Tests for config module
│   └── test_thread_context.py
│
└── docs/
    ├── Architecture.md
    ├── API.md
    ├── DeveloperGuide.md   # This file
    ├── Accessibility.md
    ├── Deployment.md
    ├── Troubleshooting.md
    └── FAQ.md
```

---

## Running Tests

```bash
# Run all tests
make test

# Run a specific test file
pytest tests/test_tools.py -v

# Run with coverage
make test-cov
```

Tests are designed to run **without any API keys** — the `clear_env_keys`
fixture in `conftest.py` strips API keys from the environment automatically.
This means tests exercise the offline fallback paths, which is exactly what
we want: the offline paths must always work.

---

## Code Quality Tools

```bash
# Lint (ruff)
make lint

# Auto-format and fix lint issues
make format

# Type checking (mypy)
make typecheck

# All checks at once
make check
```

The CI pipeline runs all three checks on every PR.

---

## Adding a New Tool

1. **Define the Python function** in `tools.py`:
   ```python
   def my_new_tool(deps: Any = None, param: str = "", **_: Any) -> str:
       """Tool docstring (Google style).

       Args:
           deps: ClarionDeps instance.
           param: Description of the parameter.

       Returns:
           A formatted string response.
       """
       result = _llm(SYSTEM_PROMPT, param)
       if result:
           return result
       return "Offline fallback response."
   ```

2. **Add the tool schema** to `TOOL_SCHEMA` in `agent.py` (OpenAI function-
   calling format).

3. **Register the implementation** in `_TOOL_IMPLS` in `agent.py`.

4. **Add a Slack shortcut** (optional) in `manifest.json` and wire it up in
   `listeners/shortcuts/__init__.py`.

5. **Write an offline test** in `tests/test_tools.py`.

---

## Environment Variables

See [.env.example](../.env.example) for the full list with descriptions.

The key variables for development:

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | Bot user OAuth token (xoxb-...) |
| `SLACK_APP_TOKEN` | App-level token for Socket Mode (xapp-...) |
| `OPENROUTER_API_KEY` | OpenRouter API key for text models |
| `GEMINI_API_KEY` | Google Gemini API key for vision |

All other variables have sensible defaults or are optional.

---

## Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app.
2. Choose **From a manifest**.
3. Paste the contents of `manifest.json` from this repository.
4. Click **Install to workspace**.
5. Copy the **Bot User OAuth Token** to `SLACK_BOT_TOKEN` in your `.env`.
6. Go to **App-Level Tokens**, create a token with `connections:write`, copy it
   to `SLACK_APP_TOKEN`.

---

## Making a Release

1. Update the version in `pyproject.toml`.
2. Add a new entry to `CHANGELOG.md` under `## [x.y.z] — YYYY-MM-DD`.
3. Commit: `git commit -m "chore: release vx.y.z"`.
4. Tag: `git tag vx.y.z`.
5. Push: `git push && git push --tags`.
6. The release workflow creates the GitHub Release automatically.
