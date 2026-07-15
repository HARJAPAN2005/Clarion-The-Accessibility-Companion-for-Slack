# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | Yes                |
| < 1.0   | No                 |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

Clarion handles Slack messages, user preferences, and AI API keys. Security
matters here. If you discover a vulnerability, please follow responsible
disclosure:

### Process

1. **Email or use GitHub's private vulnerability reporting** — go to
   [Security Advisories](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/security/advisories)
   and click **Report a vulnerability**.

2. **Include the following** in your report:
   - A description of the vulnerability and its impact
   - Steps to reproduce it (proof-of-concept code is helpful)
   - The affected version(s)
   - Any suggested fix, if you have one

3. **We will acknowledge** your report within **48 hours** and provide a
   timeline for a fix within **7 days**.

4. **We will credit you** in the release notes unless you prefer anonymity.

5. **Please do not disclose** the vulnerability publicly until we have had a
   reasonable opportunity to address it (typically 90 days).

---

## Security Considerations for Operators

When deploying Clarion, keep the following in mind:

### API Keys and Secrets

- Store all credentials in environment variables. **Never commit `.env` to git.**
- Rotate API keys regularly, especially if a team member with access departs.
- Use least-privilege scopes on your Slack bot token. The required scopes are
  documented in `manifest.json` and `.env.example`.

### Slack Token Scopes

Clarion requires only these bot token scopes:
- `app_mentions:read`, `chat:write`, `im:history`, `im:read`, `im:write`
- `channels:history`, `channels:read`, `groups:history`, `groups:read`
- `files:read`, `reactions:read`, `reactions:write`
- `users:read`, `assistant:write`, `metadata.message:read`

Do not grant additional scopes unless you have modified the code to use them.

### Data Handling

- Clarion does **not** persist message content. All message processing is
  ephemeral.
- The in-memory preference store (`thread_context.py`) is cleared on restart.
  User preferences are not stored to disk by default.
- Message content is sent to third-party AI providers (OpenRouter, Google
  Gemini). Review their data processing agreements for your compliance needs.
- Image data is base64-encoded and sent to vision models. Consider whether
  your images contain sensitive information before enabling image descriptions.

### Prompt Injection

Clarion passes user-supplied text directly to language models. Malicious users
in your Slack workspace could attempt prompt injection attacks. Clarion's system
prompt explicitly instructs the model to focus on accessibility tasks, but this
is a defence-in-depth concern rather than a hard boundary.

### Dependency Vulnerabilities

Run `make audit` (or `pip-audit -r requirements.txt`) regularly to check for
known vulnerabilities in Clarion's dependencies.
