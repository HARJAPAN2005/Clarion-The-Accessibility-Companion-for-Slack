# API Reference

This document describes the internal Python API for Clarion's accessibility
tools and agent interface. Use this reference when adding new tools, writing
tests, or integrating Clarion's tools into other code.

---

## Tools (`tools.py`)

All tools share the same calling convention:

```python
result: str = tool_function(deps=deps, **kwargs)
```

- `deps` is a `ClarionDeps` instance (see [Agent Interface](#agent-interface)).
- All tools accept `**_: Any` to absorb extra kwargs from the agent dispatcher.
- All tools return a `str` — never raise exceptions to the caller.
- All tools have a graceful offline fallback when AI is unavailable.

---

### `simplify_text`

Rewrite text into plain language at a specified reading level.

```python
def simplify_text(
    deps: Any = None,
    text: str = "",
    reading_level: str = "plain",
    language: str | None = None,
    **_: Any,
) -> str:
```

**Parameters**

| Name | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | `""` | The text to simplify. |
| `reading_level` | `str` | `"plain"` | One of `grade5`, `grade8`, `plain`, `concise`. |
| `language` | `str \| None` | `None` | Optional ISO language name for translation output. |

**Reading levels**

| Level | Audience description |
|---|---|
| `grade5` | A 10-year-old reading for the first time |
| `grade8` | A 13-year-old, using simple sentences |
| `plain` | A busy adult who reads quickly (default) |
| `concise` | Someone who needs only the critical essentials |

**Returns**: A plain-language rewrite wrapped in Clarion's standard formatting,
or a rule-based fallback if AI is unavailable.

---

### `summarize_thread`

Produce a structured catch-up digest for a Slack thread.

```python
def summarize_thread(
    deps: Any = None,
    channel_id: str = "",
    thread_ts: str = "",
    **_: Any,
) -> str:
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `channel_id` | `str` | The Slack channel ID containing the thread. |
| `thread_ts` | `str` | The timestamp of the thread's root message. |

**Returns**: A structured digest with decisions, action items, deadlines, and
open questions. Returns a placeholder message if the thread is empty or
inaccessible.

**Note**: Requires `deps.client` to be a valid `slack_sdk.WebClient` for
thread message fetching via the Web API (or Slack MCP Server when enabled).

---

### `generate_alt_text`

Generate screen-reader alt-text and a full visual description for an image.

```python
def generate_alt_text(
    deps: Any = None,
    image_url: str = "",
    context: str = "",
    **_: Any,
) -> str:
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `image_url` | `str` | The Slack private URL or permalink of the image. |
| `context` | `str` | Surrounding message text for additional context (optional). |

**Returns**: A two-part response with a concise alt-text sentence (under 125
characters) and a thorough visual description.

**Model selection**: Prefers the Gemini API (`GEMINI_API_KEY`) for image
understanding. Falls back to an OpenRouter vision model
(`OPENROUTER_VISION_MODEL`) when Gemini is not configured.

---

### `define_term`

Define an acronym or jargon term with live workspace context.

```python
def define_term(
    deps: Any = None,
    term: str = "",
    channel_id: str = "",
    **_: Any,
) -> str:
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `term` | `str` | The acronym or jargon term to define. |
| `channel_id` | `str` | Scopes the Real-Time Search to a specific channel (optional). |

**Returns**: A three-part response: plain-language definition, how the team
uses the term, and a realistic usage example.

---

### `inclusive_check`

Check a draft message for barriers to inclusive communication.

```python
def inclusive_check(
    deps: Any = None,
    text: str = "",
    **_: Any,
) -> str:
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `text` | `str` | The draft message text to review. |

**Returns**: A coaching-style review with specific flags and improved
alternatives. Returns a positive confirmation if no barriers are found.

---

## Agent Interface (`agent.py`)

### `ClarionDeps`

Runtime dependencies passed through the agent and tool call chain.

```python
@dataclass
class ClarionDeps:
    client: Any         # slack_sdk.WebClient
    user_id: str | None = None
    channel_id: str | None = None
    prefs: dict[str, Any] = field(default_factory=dict)
```

**Attributes**

| Name | Type | Description |
|---|---|---|
| `client` | `WebClient` | Slack Web API client for thread fetching and reactions. |
| `user_id` | `str \| None` | Slack user ID of the requesting user. |
| `channel_id` | `str \| None` | Slack channel ID where the request originated. |
| `prefs` | `dict` | Per-user preferences (reading level, language, auto alt-text). |

---

### `run_clarion`

Run one turn of the Clarion agent loop.

```python
def run_clarion(
    prompt: str,
    deps: ClarionDeps,
    on_chunk: Callable[[str], None] | None = None,
) -> str:
```

**Parameters**

| Name | Type | Description |
|---|---|---|
| `prompt` | `str` | The user's message or constructed prompt text. |
| `deps` | `ClarionDeps` | Runtime dependencies. |
| `on_chunk` | `Callable \| None` | Optional callback for streaming text fragments. |

**Returns**: The final text response from the agent.

---

## Config (`config.py`)

### `get_openai_client`

```python
def get_openai_client() -> openai.OpenAI | None:
```

Returns a cached OpenAI-compatible client pointed at OpenRouter. Returns
`None` when `OPENROUTER_API_KEY` is not set.

### `get_gemini_client`

```python
def get_gemini_client() -> openai.OpenAI | None:
```

Returns a cached OpenAI-compatible client pointed at the Gemini API. Returns
`None` when `GEMINI_API_KEY` is not set.

### `Settings`

```python
@dataclass(frozen=True)
class Settings:
    @classmethod
    def load(cls) -> "Settings": ...
```

Immutable snapshot of all configuration values read from environment variables.
Call `Settings.load()` to create an instance.

---

## Thread Context (`thread_context.py`)

### `PrefStore`

```python
class PrefStore:
    def get(self, user_id: str) -> dict[str, Any]: ...
    def set(self, user_id: str, **updates: Any) -> dict[str, Any]: ...
```

Thread-safe per-user preference store. Default preferences:

```python
DEFAULT_PREFS = {
    "reading_level": "plain",
    "language": None,
    "auto_alt_text": True,
}
```

### `SessionStore`

```python
class SessionStore:
    def start_session(self, channel: str, thread_ts: str, session_id: str) -> None: ...
    def get_session(self, channel: str, thread_ts: str) -> str | None: ...
```

Thread-safe session tracker. Returns `None` for unknown sessions.

### Module-level singletons

```python
session_store = SessionStore()
pref_store = PrefStore()
```

Import these singletons directly rather than instantiating new stores.
