# ⏱️ Do-this-now plan (deadline: Jul 13, 5:00pm PDT)

The code, architecture diagram, and all submission copy are done. What's left
*only you can do* (it needs your Slack account and a screen recording). Here's the
fastest safe path — about **2 hours** of work, leaving buffer.

## Step 1 — Get it running (≈40 min)
1. Install the Slack CLI + log in:
   ```bash
   curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash
   slack login
   ```
2. At <https://api.slack.com/apps> → **Create New App → From manifest** → paste
   `manifest.json` → create → **Install to Workspace**.
3. Copy **Bot Token** (`xoxb-…`) and create an **App-Level Token** with
   `connections:write` (`xapp-…`).
4. `cp .env.sample .env`, fill in `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, and
   (recommended) `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, and `OPENROUTER_VISION_MODEL`.
5. `slack run` → DM the bot "Simplify this: …" to confirm it replies.

> Short on time or hitting API issues? It runs **without** an OpenRouter key using
> built-in fallbacks — good enough to demo every feature.

## Step 2 — Grant judge access (≈5 min) — don't skip, it's required
Invite both to your sandbox workspace:
- `slackhack@salesforce.com`
- `testing@devpost.com`

## Step 3 — Stage the demo props (≈15 min)
In a channel like `#project-atlas`, post: the jargon message (Prop A in
`DEMO_SCRIPT.md`), a ~10-message thread, and one image. Open App Home in a tab.

## Step 4 — Record the video (≈30 min incl. retakes)
Follow `DEMO_SCRIPT.md` beat by beat. Screen-record, talk over it, keep it under
3 minutes. Upload unlisted to YouTube.

## Step 5 — Submit on Devpost (≈20 min)
- Paste the copy from `SUBMISSION.md`.
- Upload `assets/architecture.png` as the architecture diagram.
- Paste your **video link** and **sandbox URL**.
- Confirm the two judge emails have access.
- (Optional) push the repo to GitHub and link it.
- **Hit submit with time to spare.**

---

## Priority order if you run out of time
1. ✅ Working bot + judge access + sandbox URL  ← *without this you can't be judged*
2. ✅ 3-min demo video  ← *heaviest single judging input*
3. ✅ Architecture diagram (already made)
4. ✅ Text description (already written)
5. Repo link (nice to have)

## A note on tracks
This is submitted to **Slack Agent for Good** — it only needs the sandbox URL,
video, description, and diagram. It does **not** require Slack Marketplace
submission or 5 installed workspaces (that's the *Organizations* track, which
isn't realistic in the time left). You're on the right track for the deadline.
