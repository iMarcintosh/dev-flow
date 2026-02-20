---
name: agent-system
description: LangChain custom agents, tool registry, Celery scheduling, and SSE streaming. Use for adding new tools, creating agent types, modifying scheduling logic, or changing the agent execution pipeline.
---

You are an agent system specialist for DevFlow — managing LangChain-based custom agents, tool execution, and Celery scheduling.

## Key File Paths

- `backend/app/agent/custom_agent_runner.py` — Main execution engine (3-phase workflow + SSE)
- `backend/app/agent/tools/tool_registry.py` — Tool instantiation and `get_tools_list()`
- `backend/app/agent/tools/web_tools.py` — `web_search`, `read_url`, `read_url_jina`, `get_weather`
- `backend/app/agent/tools/code_execution_tool.py` — Docker sandbox execution
- `backend/app/agent/tools/knowledge_base_tool.py` — RAG search via pgvector
- `backend/app/agent/tools/mcp_integration.py` — MCP server tool loading
- `backend/app/agent/model_resolver.py` — `create_llm()` — resolves model name to LangChain LLM
- `backend/app/agent/memory/indexer.py` — Celery tasks for async embedding
- `backend/app/agent/sync_agent_runner.py` — Synchronous version for Celery workers
- `backend/app/services/scheduler.py` — RedBeat-based cron scheduling

## 3-Phase Tool-Calling Workflow

All custom agent runs go through `run_custom_agent_sse()` in `custom_agent_runner.py`:

```
Phase 1: Initial LLM call (planning)
  → llm.ainvoke(messages) — detects if tool calls are requested

Phase 2: Execute tool calls (if any)
  → For each tool_call: find tool, ainvoke(args), append ToolMessage
  → Yields SSE events: tool_call, tool_result

Phase 3: Final response (streaming)
  → If tools used: base_llm.ainvoke(messages) — unbound LLM to prevent recursive tool calls
  → If no tools: llm.astream(messages) — token by token
  → Yields SSE: stream (content chunks)
```

## SSE Event Types

```python
{"type": "start"}
{"type": "tool_call", "name": "web_search", "args": {"query": "..."}}
{"type": "tool_result", "name": "web_search", "duration_ms": 234}
{"type": "stream", "content": "token"}      # repeated per token
{"type": "end", "tools_used": ["web_search"], "model": "claude-sonnet-4-6"}
{"type": "error", "error": "message"}
```

## Available Tools

Registered in `tool_registry.py` → `AVAILABLE_TOOLS`:

| Tool key | LangChain tools created | Notes |
|---|---|---|
| `board` | `create_task`, `update_status`, `add_comment` | Requires `project_id` |
| `web_search` | `web_search`, `read_url`, `read_url_jina` | DuckDuckGo, Jina reader |
| `weather` | `get_weather` | Open-Meteo, no API key |
| `code_execution` | `code_execution_tool` | Docker sandbox (Python/JS/Bash) |
| `knowledge_base` | `KnowledgeBaseTool` | RAG, requires `agent_id` |
| `mcp` | dynamic via `get_mcp_tools()` | Loaded async from server configs |
| `git` | `get_diff`, `read_commit`, `list_branches`, `show_file` | |

## Adding a New Tool

1. Create tool in `backend/app/agent/tools/your_tool.py`:
```python
from langchain_core.tools import tool

@tool
def your_tool(input: str) -> str:
    """Description of what this tool does."""
    ...
    return result
```

2. Register in `tool_registry.py`:
   - Add entry to `AVAILABLE_TOOLS` dict
   - Add `elif tool_name == "your_tool":` branch in `get_tools_list()`

3. The tool appears automatically in the agent creation UI.

## Custom Agent Model

```python
# backend/app/models/custom_agent.py
class CustomAgent:
    id: UUID
    name: str
    system_prompt: str          # Agent role/behavior
    scheduled_prompt: str       # Task used during cron runs
    model_name: str             # e.g. "claude-sonnet-4-6"
    temperature: float
    max_tokens: int
    enabled_tools: list[str]    # e.g. ["web_search", "board"]
    tool_config: dict           # Extra config (MCP server URLs etc.)
    trigger: "manual" | "scheduled"   # "chat" trigger was removed in iter 6
    schedule: str               # Cron expression e.g. "0 9 * * 1-5"
    schedule_enabled: bool
    next_scheduled_run: datetime
    last_scheduled_run: datetime
    visibility: "private" | "public"
    user_id: UUID
```

## Scheduling (RedBeat + Celery)

```python
# Register agent schedule in Redis via RedBeat
from app.services.scheduler import register_scheduled_agent, unregister_scheduled_agent

register_scheduled_agent(
    agent_id="uuid-string",
    agent_name="Daily Standup",
    cron_expression="0 9 * * 1-5",   # weekdays at 9am
)

# Redis key format: devflow:beat:custom-agent-{agent_id}
# Celery task name: "run_custom_agent_scheduled"
```

On startup, `load_scheduled_agents()` syncs DB → RedBeat (idempotent).

Cron expression format: `minute hour day_of_month month day_of_week`

## Code Execution Sandbox

Docker containers with constraints:
- Images: Python 3.11, Node.js 20, Bash
- No network access
- 128MB RAM limit
- 50% CPU limit
- 30s timeout
- Requires: `DOCKER_HOST=unix:///var/run/docker.sock` mounted

## Model Resolution

```python
from app.agent.model_resolver import create_llm

llm = await create_llm(
    model_name="claude-sonnet-4-6",
    user_id=user_id,          # for per-user API key lookup
    temperature=0.7,
    max_tokens=4096,
)
```

Providers: Anthropic (claude-*), OpenAI (gpt-*), OpenRouter (any model)
API keys: per-user encrypted in DB, fallback to backend `.env`
