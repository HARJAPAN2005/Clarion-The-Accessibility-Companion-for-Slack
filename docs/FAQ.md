# FAQ

Frequently asked questions about Clarion.

---

## General

**What is Clarion?**

Clarion is an AI-powered Slack application that makes workplace communication
more accessible. It rewrites complex messages into plain language, summarises
long threads, generates alt-text for images, defines jargon, and reviews
drafts for inclusive language.

**Is Clarion free to use?**

Clarion is open-source software under the MIT License — free to use, modify,
and distribute. Running Clarion requires a Slack workspace, and AI features
require an OpenRouter or Google Gemini API key, which have their own pricing.
OpenRouter offers free models that work well for evaluation.

**Does Clarion store my messages?**

Clarion does not persist message content to disk. All processing is ephemeral
— messages are sent to the AI provider for processing and discarded. User
preferences (reading level, language) are stored in memory and cleared on
restart.

**Will Clarion respond to every message in a channel?**

No. Clarion only responds when explicitly invoked:
- `@Clarion` mentioned in a channel
- A direct message to Clarion
- A message shortcut used from the `···` menu
- A follow-up in a thread where Clarion has already responded

Clarion does not monitor channels passively.

---

## Features

**What reading levels does simplification support?**

Four levels: Grade 5 (very simple), Grade 8 (plain language), Plain (clear
for a busy adult, default), and Concise (key points only). Set your preferred
level in the Clarion App Home.

**Can Clarion translate messages?**

Yes — select your preferred language in the App Home. Clarion will write its
simplified output in that language. Supported: Spanish, French, Hindi,
Mandarin, Arabic, Portuguese (and any language supported by the underlying
model).

**Does Clarion work with images shared as links?**

The **Describe image** shortcut only works on images that were uploaded directly
to Slack as file attachments, not images shared as URLs. Slack's API provides
authenticated access to uploaded files but not to external links.

**Can Clarion summarise a thread in a private channel?**

Yes, as long as Clarion has been invited to the channel (`/invite @Clarion`)
and the bot token has the `groups:history` scope.

**What is the Slack MCP Server?**

The Model Context Protocol (MCP) Server is a Slack-provided mechanism for
AI applications to read thread history in a governed, enterprise-friendly way.
Clarion uses it when running in HTTP + OAuth mode with `SLACK_MCP_ENABLED=true`.
In Socket Mode, Clarion falls back to the standard `conversations.replies`
Web API.

---

## Technical

**What AI models does Clarion use?**

By default: `poolside/laguna-xs-2.1:free` for text (via OpenRouter) and
`gemini-2.0-flash` for vision (via Google Gemini). Both can be overridden with
environment variables. Any OpenRouter-compatible model works for text.

**What happens when the AI is unavailable?**

Every tool has a deterministic offline fallback. For example:
- **simplify_text** — applies rule-based jargon replacement
- **inclusive_check** — uses pattern matching against a known barrier list
- **define_term** — returns from a built-in demo glossary
- **summarize_thread** — returns a skeleton digest with message count
- **generate_alt_text** — returns a helpful prompt asking the author to add
  a description

**Can I run Clarion without any API keys?**

Yes. The offline fallbacks mean every feature returns *something* useful. The
experience is less polished without AI, but the app never dead-ends.

**Does Clarion support multiple Slack workspaces?**

Yes — when running in HTTP + OAuth mode (`app_oauth.py`). Socket Mode supports
only the workspace you are logged into.

**How do I add a new language to the preference menu?**

Add the language to the options list in `listeners/views/home.py`. The
underlying model handles the translation — no additional configuration is needed.

---

## Contributing

**How do I contribute?**

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full guide. The short version:
fork the repo, make your changes on a branch, run `make check`, and open a
pull request.

**Where should I ask for help?**

[GitHub Discussions](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/discussions)
is the best place for questions. For bugs, use the
[Bug Report](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/issues/new?template=bug_report.yml)
template.

**Is there a roadmap?**

Yes — see [ROADMAP.md](../ROADMAP.md).
