# Contributing to Clarion

Thank you for your interest in making Slack more accessible. Every contribution
matters — whether it's a bug fix, a new accessibility feature, an improvement
to the docs, or simply helping another user in a Discussion.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Commit Message Format](#commit-message-format)
- [Good First Issues](#good-first-issues)
- [Reporting Security Vulnerabilities](#reporting-security-vulnerabilities)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you agree to uphold it. Please report unacceptable behaviour to
the maintainers via the contact address in [SECURITY.md](SECURITY.md).

---

## How Can I Contribute?

### Report a Bug

Search the [existing issues](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/issues)
before opening a new one. When reporting, please use the **Bug Report** issue template and include:

- Steps to reproduce the problem
- What you expected to happen
- What actually happened
- Your environment (OS, Python version, Slack Bolt version)

### Request a Feature

Open a [Feature Request](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/issues/new?template=feature_request.yml).
Describe the user problem you are solving, not just the solution.

### Report an Accessibility Issue

Use the dedicated [Accessibility Issue](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/issues/new?template=accessibility_issue.yml)
template. Clarion is an accessibility tool — accessibility issues are first-class concerns.

### Improve the Documentation

Even small documentation improvements (typo fixes, clarified examples) are welcomed.
Use the **Documentation Improvement** template.

### Submit a Pull Request

See [Submitting a Pull Request](#submitting-a-pull-request) below.

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- A Slack workspace where you can install apps
- A Slack app created at [api.slack.com/apps](https://api.slack.com/apps)

### Local Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/Clarion-The-Accessibility-Companion-for-Slack.git
cd Clarion-The-Accessibility-Companion-for-Slack

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install all dependencies (including dev extras)
pip install -e ".[dev]"
# or: make install

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 5. Start Clarion in Socket Mode
python app.py
# or: make dev
```

### Running Tests

```bash
# Run the full test suite
make test

# Run with coverage report
make test-cov

# Run a specific test file
pytest tests/test_tools.py -v
```

### Linting and Formatting

```bash
# Check for lint errors
make lint

# Auto-format and fix lint issues
make format

# Run type checking
make typecheck
```

---

## Project Structure

```
clarion/
├── app.py               Entry point — Socket Mode
├── app_oauth.py         Entry point — HTTP + OAuth (Slack MCP Server)
├── agent.py             AI agent loop and tool dispatch
├── tools.py             The five accessibility tool implementations
├── config.py            Centralized configuration and AI client factories
├── thread_context.py    In-memory session and preference stores
├── rts_client.py        Real-Time Search API client
├── slack_mcp.py         Slack MCP Server helper
├── listeners/
│   ├── events/          Slack event handlers
│   ├── actions/         Slack action handlers (buttons, selects)
│   ├── shortcuts/       Slack message shortcut handlers
│   └── views/           Block Kit view builders
├── tests/               Pytest test suite
├── docs/                Documentation
└── .github/             CI/CD and community templates
```

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) with a 100-character line limit.
- All functions, classes, and modules must have **Google-style docstrings**.
- Use **type annotations** on all public functions.
- Prefer `from __future__ import annotations` for forward references.
- Use `f-strings` for string formatting. Avoid `%`-style or `.format()`.

### Tool Implementations

Every tool in `tools.py` must:

1. Degrade gracefully — return a meaningful response when no API key is set.
2. Accept `**_: Any` to absorb extra kwargs from the agent dispatch layer.
3. Use `_llm()` for all AI calls — never construct a client directly in a tool.
4. Have a unit test in `tests/test_tools.py` covering the offline path.

### Logging

Use the module-level `logger = logging.getLogger("clarion.<module>")` pattern.
Do **not** use `print()` anywhere in production code.

### Error Handling

- Catch the most specific exception type possible.
- Log exceptions with `logger.exception()` (which includes the traceback).
- Never silently swallow exceptions in user-facing code.
- Event handlers must catch and log all exceptions to prevent Bolt timeouts.

---

## Submitting a Pull Request

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes** following the coding standards above.

3. **Write or update tests** — new features require test coverage.

4. **Run the full check suite**:
   ```bash
   make check   # runs lint + typecheck + test
   ```

5. **Commit** following the [commit message format](#commit-message-format).

6. **Push and open a PR** against `main`. Fill in the PR template completely.

7. **Address review feedback** — a maintainer will review within 5 business days.

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`

Examples:
```
feat(tools): add tone adjustment option to simplify_text
fix(agent): handle empty tool call arguments gracefully
docs(contributing): add commit message format section
test(thread_context): add concurrent session write test
```

---

## Good First Issues

New to the project? Look for issues tagged
[`good first issue`](https://github.com/HARJAPAN2005/Clarion-The-Accessibility-Companion-for-Slack/issues?q=is%3Aopen+label%3A%22good+first+issue%22).

Some ideas to get started:
- Add support for an additional language in the translation preference menu
- Expand the demo glossary in `rts_client.py`
- Add a test for a specific edge case in the existing tool fallbacks
- Improve inline docstrings in `listeners/`
- Translate the README into another language

---

## Reporting Security Vulnerabilities

**Do not open a public issue for security vulnerabilities.**

Please follow the process described in [SECURITY.md](SECURITY.md).
