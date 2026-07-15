# Clarion Roadmap

This document describes the planned direction for Clarion. It is a living
document — priorities may shift based on community feedback, usage data, and
the evolution of Slack's platform capabilities.

Items marked with an RFC label indicate that a design discussion should happen
before implementation begins.

---

## v1.x — Stability and Polish

These improvements are targeted for the 1.x release series and are within scope
for community contributions right now.

### Quality and Reliability

- [ ] Persistent preference store with Redis support
      (replaces the in-memory store for multi-process deployments)
- [ ] Rate limiting per user to prevent unintended AI cost spikes
- [ ] Response caching for identical inputs within a sliding window
- [ ] Configurable timeout per tool to prevent Slack interaction timeouts
- [ ] Structured JSON logging output for production log aggregation

### Accessibility Features

- [ ] Tone detector — identify and flag aggressive or dismissive phrasing
- [ ] Reading complexity score — show a Flesch-Kincaid score alongside
      the simplified version
- [ ] Bullet-point extraction — convert dense paragraphs to structured lists
- [ ] Emoji-free mode — rewrite messages that use heavy emoji substitution
      for screen-reader users
- [ ] Dyslexia-friendly font suggestion — link to browser extension resources

### Languages and Internationalisation

- [ ] Expand language menu to include Japanese, Korean, German, Italian,
      Polish, and Turkish
- [ ] Auto-detect source language before simplifying
- [ ] Bilingual output mode — show original and plain-language side by side

### Developer Experience

- [ ] `make docs` target to generate API docs with pdoc
- [ ] Pre-commit hooks configuration
- [ ] Integration tests using a Slack test workspace (sandbox mode)

---

## v2.0 — Platform Expansion

These features require more significant design work. Community RFC discussions
will be opened before implementation begins.

### Proactive Accessibility (RFC)

Instead of waiting to be invoked, Clarion monitors configured channels for
messages above a complexity threshold and automatically offers a simplified
version as a thread reply. This requires careful opt-in design to avoid spam.

### Workspace-Level Analytics Dashboard (RFC)

An App Home dashboard showing aggregated (anonymised) accessibility metrics:
most common jargon terms, simplification request volume, and team-level
readability trends over time.

### Custom Jargon Glossary (RFC)

Workspace admins can maintain a Clarion-specific glossary of internal terms
with their plain-language definitions. Clarion uses this glossary to ground
`define_term` results and improve `inclusive_check` accuracy.

### Slack Workflow Builder Integration

Native Clarion steps for Slack Workflow Builder, allowing teams to add
auto-simplification or thread digest steps to any automated workflow without
writing code.

### OpenTelemetry Observability

Structured traces and metrics compatible with OpenTelemetry, enabling
operators to instrument Clarion with their existing APM stack (Datadog,
Grafana, Honeycomb, etc.).

---

## Future Ideas (No Timeline)

The following ideas have been proposed by the community or the maintainers but
have no scheduled implementation timeline. Open a Discussion to champion one.

- Native Slack Huddle transcript simplification
- Clarion CLI for simplifying text outside of Slack
- Browser extension for Slack Web
- Integration with external translation memory tools (DeepL, Google Translate)
- Accessibility audit mode — scan an entire channel for historical jargon usage
- Support for Slack Connect channels across workspace boundaries

---

## Completed

See [CHANGELOG.md](CHANGELOG.md) for all completed work.
