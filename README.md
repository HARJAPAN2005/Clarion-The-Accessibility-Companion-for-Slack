# ⚓ Clarion — the accessibility layer for Slack

**Slack Agent Builder Challenge · Track: Slack Agent for Good (Accessibility)**

Clarion makes every Slack conversation accessible to everyone — neurodivergent
colleagues, people with cognitive or reading differences, non-native English
speakers, people who are blind or have low vision, and anyone joining a thread
late. It's an *inclusion layer* that works wherever your team already works.

It uses **all three** eligible challenge technologies:

| # | Technology | How Clarion uses it |
|---|------------|---------------------|
| ① | **Slack AI capability** (Claude Agent SDK) | plain-language rewrites, alt-text, catch-up digests, tone checks |
| ② | **Slack MCP Server** | reads thread history the governed way to build catch-up digests |
| ③ | **Real-Time Search API** | defines acronyms & jargon from *live* workspace context |

---

## What it does

- **Simplify** — rewrites jargon-heavy messages into clear plain language, keeping every decision, owner, date and action item. (`@Clarion simplify`, DM, or the *Simplify this message* shortcut)
- **Catch me up** — turns a long thread into a plain-language digest: the decision, who owns what, deadlines, what's still open.
- **Describe image** — generates screen-reader alt-text for images (a real accessibility gap in Slack today).
- **Define a term** — explains an acronym or piece of internal shorthand using live workspace context via the Real-Time Search API.
- **Inclusive check** — flags idioms, unexplained acronyms, and exclusionary phrasing in a draft before it's sent.
- **Per-user preferences** in App Home: reading level, output language, auto alt-text.

Clarion greets users with 👀 while it works and ✅ when it's done, streams its
answer in as it writes, and shows "thinking" statuses — using the Bolt agent
UI primitives.

---

## Quick start (Socket Mode — for the demo)

> Requires the **Slack CLI v4+** and Python 3.10+.

```bash
# 1. Install the Slack CLI (if you haven't)
curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash
slack login

# 2. Get the code + secrets
cp .env.sample .env      # then fill in SLACK_BOT_TOKEN, SLACK_APP_TOKEN, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_VISION_MODEL

# 3. Run it
slack run
```

Then in Slack: DM Clarion, `@Clarion` it in a channel, or use the message
shortcuts (the `···` menu on any message).

> **No OpenRouter key handy?** Clarion still runs. Every tool has a deterministic
> offline fallback so the demo never dead-ends — you'll see mechanical
> simplification, the RTS demo glossary, and rule-based inclusive checks.

### Creating the app from the manifest

If you're wiring the app up by hand at <https://api.slack.com/apps>: create a new
app **from manifest**, paste `manifest.json`, install to your workspace, then copy
the **Bot Token** (`xoxb-…`) and an **App-Level Token** with `connections:write`
(`xapp-…`) into `.env`.

---

## Enable the Slack MCP Server (technology ②)

The catch-up digest reads thread history through the **Slack MCP Server** when
Clarion runs in HTTP/OAuth mode:

```bash
ngrok http 3000
# in manifest.json: set socket_mode_enabled=false and point redirect_urls at your ngrok domain
slack install -E local
# slack app settings → Agents → toggle "Model Context Protocol" ON
# copy Client ID / Secret / Signing Secret + your ngrok redirect into .env
export SLACK_MCP_ENABLED=true
slack run app_oauth.py
```

Open the install URL the CLI prints to install via OAuth. In Socket Mode the same
digest works through `conversations.replies` as a fallback, so you can demo either way.

---

## Wire up the Real-Time Search API (technology ③)

Set `SLACK_RTS_TOKEN` (and optionally `SLACK_RTS_ENDPOINT`) in `.env`. Without a
token, `define_term` uses a small built-in workspace glossary (RTS, OKR, P1, EOD)
so the feature is fully demoable offline.

---

## Project layout

```
clarion/
├── manifest.json            # app definition: scopes, events, shortcuts, agent config
├── app.py                   # Socket Mode entry point
├── app_oauth.py             # HTTP + OAuth entry (enables the Slack MCP Server)
├── agent.py                 # Claude Agent SDK loop + tool schema
├── tools.py                 # the 5 accessibility tools (all with offline fallbacks)
├── rts_client.py            # Real-Time Search API client
├── slack_mcp.py             # Slack MCP Server helper (Web API fallback)
├── thread_context.py        # session + per-user preference store
├── listeners/
│   ├── events/              # app_mention, message, app_home_opened
│   ├── actions/             # feedback buttons + Home preference controls
│   ├── shortcuts/           # simplify / alt-text / catch-me-up message shortcuts
│   ├── views/               # Home tab + feedback Block Kit
│   └── _stream.py           # defensive say_stream helper
└── assets/architecture.(svg|png)
```

---

## Grant judges access (required for submission)

Invite both accounts to your developer sandbox workspace so they can test Clarion:

- `slackhack@salesforce.com`
- `testing@devpost.com`

Then put your sandbox URL in the Devpost submission.

---

Built for the Slack Agent Builder Challenge. Powered by Slack AI, the Slack MCP
Server, and the Real-Time Search API.
