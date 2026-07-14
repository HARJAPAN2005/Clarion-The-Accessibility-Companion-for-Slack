# Clarion — Devpost submission copy

Copy/paste these into the Devpost form. Placeholders in **[brackets]** are things
only you can provide (your sandbox URL, your video link).

---

## Project name
**Clarion — the accessibility layer for Slack**

## Tagline (≤ 200 chars)
An agent that makes every Slack conversation accessible to everyone: plain-language rewrites, catch-up digests, screen-reader alt-text, and instant jargon definitions.

## Track
**Slack Agent for Good** — Accessibility & digital inclusion.

## Which of the three technologies does it use?
All three: **Slack AI capabilities**, **Slack MCP Server**, and the **Real-Time Search API**.

---

## Inspiration
Slack is where work happens — which means it's also where people get left behind.
An estimated **1 in 4 adults lives with a disability**, and a huge share of any
workforce reads in a second language or is neurodivergent. Yet the default Slack
experience is walls of jargon, unexplained acronyms, 80-message threads, and
images with no descriptions. The people most affected — those with ADHD, dyslexia,
cognitive disabilities, low vision, or limited English — are exactly the ones who
quietly fall out of the conversation. Clarion closes that gap without asking anyone
to change how they already work.

## What it does
Clarion is an **inclusion layer** you can invoke anywhere in Slack:

- **Simplify** — rewrites dense, jargon-heavy messages into clear plain language,
  preserving every decision, owner, date, and action item. Available via
  `@Clarion`, DM, or a one-click message shortcut.
- **Catch me up** — turns a long thread into a plain-language digest: *the
  decision · who owns what · deadlines · what's still open* — so people returning
  from leave or joining late aren't lost.
- **Describe image** — generates screen-reader alt-text for images, a real
  accessibility gap in Slack today.
- **Define a term** — explains an acronym or piece of internal shorthand using
  *live* workspace context, so newcomers aren't excluded by insider language.
- **Inclusive check** — flags idioms, unexplained acronyms, and exclusionary
  phrasing in a draft before it's sent.
- **Per-user preferences** in App Home: reading level (Grade 5 → Concise),
  output language for translation, and auto alt-text.

Clarion reacts 👀 while it works and ✅ when done, streams answers as it writes,
and shows friendly "thinking" statuses — using Bolt's agent UI primitives.

## How we built it
- **Bolt for Python** app scaffolded from the `slack create agent` Agent Kit
  pattern, with a clean listener router for events, actions, shortcuts, and views.
- **OpenRouter/OpenAI API** runs an agent loop over five accessibility tools; the model
  picks the right tool per request.
- **Slack MCP Server** (HTTP/OAuth mode) reads thread history for catch-up digests
  the governed, enterprise-friendly way — with a Web API fallback for Socket Mode.
- **Real-Time Search API** grounds jargon/acronym definitions in live workspace
  context rather than a stale glossary.
- **Block Kit** for the Home dashboard, digests, and feedback buttons.
- A **graceful fallback layer**: every tool returns a useful deterministic result
  even without an API key or network, so it degrades instead of breaking.

## Technologies used
Slack CLI v4 · Bolt for Python 1.28 · Slack AI / OpenRouter/OpenAI API · Slack MCP
Server · Real-Time Search API · Slack Web API · Block Kit · Python 3.11 ·
OpenRouter / OpenAI API (supports configuring separate text and vision models via `.env`).

## Challenges we ran into
Keeping meaning intact while simplifying — "plain language" must never drop a
deadline or an owner — so the prompts are tuned to preserve structured facts.
We also made every feature demoable offline so a flaky sandbox connection can't
sink the demo.

## Accomplishments we're proud of
An agent that spans four Slack surfaces (mention, DM, shortcuts, App Home), uses
all three challenge technologies meaningfully rather than as a checkbox, and
targets a genuinely underserved need.

## What we learned
Slack's Agent Kit removes almost all of the boilerplate — the real work is the
product judgment about *what* makes communication accessible.

## What's next for Clarion
Auto-alt-text on every uploaded image (opt-in), a workspace glossary that learns
from RTS over time, and a "read this to me" audio mode. We'd love to ship it to
the Slack Marketplace so any org can install it in one click.

## Impact (Slack Agent for Good)
Accessibility isn't a niche: it helps neurodivergent employees, non-native
speakers, screen-reader users, and every person catching up on a thread. Clarion's
impact is measurable — teams can track reduced time-to-catch-up, fewer "what does
X mean?" interruptions, and images shipped with alt-text. And it reaches **beyond**
the workplace: the same plain-language engine could serve nonprofits, clinics, and
government teams that communicate with vulnerable populations in Slack.

---

## Fill-in checklist for the Devpost form
- [ ] **Text description** — paste the sections above.
- [ ] **Demo video (~3 min)** — link here: **[your YouTube/Vimeo URL]** (script in `DEMO_SCRIPT.md`).
- [ ] **Architecture diagram** — upload `assets/architecture.png`.
- [ ] **Slack developer sandbox URL** — **[your sandbox URL]**.
- [ ] **Sandbox access granted** to `slackhack@salesforce.com` and `testing@devpost.com`.
- [ ] Repo link (optional but recommended) — **[your GitHub URL]**.
