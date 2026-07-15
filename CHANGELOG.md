# Changelog

All notable changes to Clarion are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.0.0] — 2024-07-15

### Added

- **`simplify_text`** — AI-powered plain-language rewrite with four reading
  levels (Grade 5, Grade 8, Plain, Concise) and optional translation output.
- **`summarize_thread`** — Structured catch-up digest for Slack threads,
  covering decisions, action items, deadlines, and open questions.
- **`generate_alt_text`** — Screen-reader alt-text and full visual description
  for images uploaded to Slack, powered by Gemini 2.0 Flash.
- **`define_term`** — Live jargon and acronym definitions grounded in
  workspace context via the Real-Time Search API.
- **`inclusive_check`** — Pre-send review of draft messages for jargon,
  idioms, and exclusionary phrasing.
- Per-user preferences (reading level, output language, auto alt-text) stored
  in the App Home and respected by every tool invocation.
- Socket Mode entry point (`app.py`) for local development.
- HTTP + OAuth entry point (`app_oauth.py`) for production and Slack MCP
  Server integration.
- Three Slack message shortcuts: **Simplify this message**, **Describe image**,
  **Catch me up**.
- Graceful offline fallback for every tool — Clarion remains useful even when
  AI services are unreachable.
- Shared `config.py` module centralising all environment variable reads and
  AI client singletons.
- `tests/` directory with offline unit tests for all five tools, config
  module, and session/preference stores.
- Multi-stage `Dockerfile` and `docker-compose.yml` for containerised
  deployment.
- Complete `.github/` with CI/CD workflows (lint, test, CodeQL, release),
  issue templates, and PR template.
- Comprehensive documentation in `docs/`.
- `Makefile` with standard developer targets.
- `.devcontainer/` for one-click VS Code dev environment setup.
- MIT License.

### Fixed

- `app.py`: replaced `print()` calls with structured `logger` output.
- `listeners/_stream.py`: defensive handling of Bolt streaming API changes
  across patch releases.

---

[Unreleased]: https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/releases/tag/v1.0.0
