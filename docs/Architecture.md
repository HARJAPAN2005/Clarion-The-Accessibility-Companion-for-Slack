# Architecture

This document describes how Clarion works internally — from receiving a Slack
event to delivering an accessible response.

---

## System Overview

Clarion is a Slack application that processes user requests through an AI agent
loop, dispatches to specialised accessibility tools, and streams results back
into Slack in real time.

```mermaid
graph TB
    User(["👤 Slack User"])
    Slack["Slack Platform"]
    Bolt["Slack Bolt Framework\n(Python)"]
    Agent["Agent Loop\nagent.py"]
    Tools["Accessibility Tools\ntools.py"]
    OpenRouter["OpenRouter API\n(text models)"]
    Gemini["Google Gemini API\n(vision model)"]
    RTS["Real-Time Search API\n(jargon definitions)"]
    MCP["Slack MCP Server\n(thread history)"]
    Prefs["Preference Store\nthread_context.py"]

    User -- "mention / DM / shortcut" --> Slack
    Slack -- "event / action / shortcut" --> Bolt
    Bolt -- "dispatches to listener" --> Agent
    Agent -- "calls tools" --> Tools
    Tools -- "text prompts" --> OpenRouter
    Tools -- "image prompts" --> Gemini
    Tools -- "jargon query" --> RTS
    Tools -- "thread fetch" --> MCP
    Agent -- "reads preferences" --> Prefs
    Agent -- "streams reply" --> Bolt
    Bolt -- "posts message" --> Slack
    Slack -- "delivers to user" --> User
```

---

## Request Flow

```mermaid
sequenceDiagram
    participant User as Slack User
    participant Slack as Slack Platform
    participant Listener as Bolt Listener
    participant Agent as Agent Loop
    participant Tool as Accessibility Tool
    participant LLM as AI Provider

    User->>Slack: @Clarion simplify this message
    Slack->>Listener: app_mention event
    Listener->>Listener: extract text, strip mention
    Listener->>Agent: run_clarion(prompt, deps)
    Agent->>LLM: chat.completions.create (streaming)
    LLM-->>Agent: tool_call: simplify_text
    Agent->>Tool: simplify_text(text=...)
    Tool->>LLM: single completion (non-streaming)
    LLM-->>Tool: simplified text
    Tool-->>Agent: result string
    Agent->>LLM: feed tool result back
    LLM-->>Agent: final text response (streaming)
    Agent-->>Listener: on_chunk callbacks
    Listener->>Slack: say_stream chunks
    Slack-->>User: streaming reply in thread
```

---

## Slack Event Flow

```mermaid
flowchart LR
    Events["Slack Events"]
    AppMention["app_mention\napp_mentioned.py"]
    MessageIM["message.im\nmessage.py"]
    AppHome["app_home_opened\napp_home_opened.py"]
    Shortcuts["Message Shortcuts\nshortcuts/__init__.py"]
    Actions["Block Kit Actions\nactions/__init__.py"]

    Events --> AppMention
    Events --> MessageIM
    Events --> AppHome
    Events --> Shortcuts
    Events --> Actions

    AppMention -->|"@mention in channel"| Agent
    MessageIM -->|"DM or thread reply"| Agent
    AppHome -->|"Home tab"| HomeView["Home View Builder"]
    Shortcuts -->|"simplify_message"| SimplifyTool["simplify_text tool"]
    Shortcuts -->|"alt_text_message"| AltTool["generate_alt_text tool"]
    Shortcuts -->|"digest_thread"| DigestTool["summarize_thread tool"]
    Actions -->|"set_reading_level"| PrefStore["PrefStore.set()"]
    Actions -->|"set_language"| PrefStore
    Actions -->|"toggle_auto_alt"| PrefStore
    Actions -->|"feedback_*"| Logger["Logger"]
```

---

## LLM Processing Pipeline

```mermaid
flowchart TD
    Start([User prompt]) --> HasKey{OPENROUTER_API_KEY set?}
    HasKey -- No --> Offline["Offline fallback\n(mechanical simplify)"]
    HasKey -- Yes --> Call["_attempt_llm_call()\nstreaming=True"]
    Call --> Success{Success?}
    Success -- Yes --> Parse["Parse streaming chunks\ncollect tool_calls + content"]
    Success -- RateLimited --> Retry["Exponential backoff retry\n(max 2 retries)"]
    Retry --> Call
    Success -- 404 --> Fallback404["Try DEFAULT_MODEL\npooside/laguna-xs-2.1:free"]
    Fallback404 --> Call
    Success -- Other error --> Offline
    Parse --> HasTools{Tool calls?}
    HasTools -- No --> Done([Return final text])
    HasTools -- Yes --> RunTool["_run_tool(name, args, deps)"]
    RunTool --> FeedBack["Append tool result\nto messages"]
    FeedBack --> Iteration{Iteration < 6?}
    Iteration -- Yes --> Call
    Iteration -- No --> MaxIter["Return fallback\nerror message"]
```

---

## Accessibility Pipeline

```mermaid
flowchart LR
    Input["User message\nor request"]

    SimplifyText["simplify_text\n• 4 reading levels\n• Jargon replacement\n• Optional translation"]
    SummarizeThread["summarize_thread\n• Thread fetch (MCP/Web API)\n• Decision extraction\n• Action item detection"]
    GenerateAltText["generate_alt_text\n• Slack image download\n• Base64 encoding\n• Vision model call"]
    DefineTerm["define_term\n• RTS API query\n• Demo glossary fallback\n• Warm plain-language output"]
    InclusiveCheck["inclusive_check\n• Barrier detection\n• Pattern matching fallback\n• Coaching tone"]

    Input --> SimplifyText
    Input --> SummarizeThread
    Input --> GenerateAltText
    Input --> DefineTerm
    Input --> InclusiveCheck

    SimplifyText --> Output["Accessible\nSlack message"]
    SummarizeThread --> Output
    GenerateAltText --> Output
    DefineTerm --> Output
    InclusiveCheck --> Output
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph Local["Local Development"]
        AppPy["app.py\n(Socket Mode)"]
        SlackCLI["slack run"]
    end

    subgraph Production["Production — HTTP + OAuth"]
        AppOauth["app_oauth.py\n(HTTP + OAuth)"]
        Ngrok["ngrok / reverse proxy"]
        FileStore["FileInstallationStore\n./data/installations"]
    end

    subgraph Docker["Docker"]
        Container["clarion:latest\nMulti-stage build"]
        EnvFile[".env file"]
    end

    AppPy <--> SlackPlatform["Slack Platform\n(WebSocket)"]
    AppOauth <--> Ngrok <--> SlackPlatform
    AppOauth --> FileStore
    Container <-- env_file --> EnvFile
    Container --> AppPy
```

---

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Socket Mode entry point, startup diagnostics |
| `app_oauth.py` | HTTP + OAuth entry point, Slack MCP Server |
| `agent.py` | AI agent loop, tool dispatch, streaming |
| `tools.py` | Five accessibility tool implementations |
| `config.py` | Environment variables, AI client singletons |
| `thread_context.py` | Session tracking, user preferences |
| `rts_client.py` | Real-Time Search API client |
| `slack_mcp.py` | Slack MCP Server / Web API bridge |
| `listeners/events/` | Slack event handlers (mention, DM, home) |
| `listeners/actions/` | Block Kit button and select handlers |
| `listeners/shortcuts/` | Message shortcut handlers |
| `listeners/views/` | Block Kit view builders (home, feedback) |
| `listeners/_stream.py` | Defensive Bolt streaming helper |
