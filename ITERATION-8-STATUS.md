# DevFlow - Iteration 8 Status

**Date:** 2026-03-12
**Focus:** Per-User API Key Isolation + Embedding Fixes + Agent Chat Streaming
**Status:** ✅ **COMPLETE**

---

## 🎯 Iteration Goals

1. ✅ Per-user model cache isolation (Redis key scoped to user ID)
2. ✅ OpenAI embedding key propagated per-user to KnowledgeBaseTool
3. ✅ Extended OpenAI fallback model list (GPT-5, o3, o1)
4. ✅ Agent Chat: no-flicker fix for assistant response
5. ✅ Agent Chat: rotating conic-gradient border as streaming indicator

---

## ✅ Completed Changes

### A) Per-User Isolation (Backend)

#### `backend/app/api/routes/models.py`

**Root Cause:**
Model cache was stored under a shared key (`available_models`) in Redis, meaning all users saw the same model list regardless of their individual API keys. A user with an OpenRouter key would see the same (empty) OpenRouter model list as a user without one.

**Fix:**
Cache key is now scoped per user: `available_models:{user_id}`. Both `GET /api/models` and `POST /api/models/refresh` resolve per-user OpenAI and OpenRouter keys via `api_key_service` before fetching and caching.

```python
cache_key = f"available_models:{current_user.id}"
openai_key = await api_key_service.get_api_key(db, str(current_user.id), "openai") or ""
openrouter_key = await api_key_service.get_api_key(db, str(current_user.id), "openrouter") or ""
```

#### `backend/app/services/model_discovery.py`

**Change:** Extended `OPENAI_MODELS_FALLBACK` with current model families (as of 2026):
- GPT-5, GPT-5 Mini (flagship 2026, 1M context)
- GPT-4.1, GPT-4.1 Mini, GPT-4.1 Nano (1M context)
- o3, o3-mini (advanced reasoning)
- o1, o1-mini (reasoning models)

`fetch_openai_models()` filters live API results to only current prefixes (`gpt-5`, `gpt-4.1`, `gpt-4o`, `o1`, `o3`, `o4`) and excludes deprecated preview/versioned suffixes.

#### `backend/app/agent/tools/knowledge_base_tool.py`

**Root Cause:**
`KnowledgeBaseTool` had no field for the OpenAI API key — the embedding call in `knowledge_base_service.search_knowledge_base()` always used the global `settings.openai_api_key`, ignoring the user's personal key.

**Fix:**
Added `api_key: str = ""` field to `KnowledgeBaseTool`. The key is passed through to `search_knowledge_base(api_key=self.api_key or None)`.

```python
class KnowledgeBaseTool(BaseTool):
    api_key: str = ""   # OpenAI API key for embeddings (per-user)

    def _run(self, query: str) -> str:
        results = knowledge_base_service.search_knowledge_base(
            agent_id=self.agent_id,
            query=query,
            n_results=3,
            api_key=self.api_key or None,
        )
```

#### `backend/app/agent/tools/tool_registry.py`

**Change:** `get_tools_list()` now accepts `embedding_api_key: str = ""` and forwards it when constructing `KnowledgeBaseTool`:

```python
kb_tool = KnowledgeBaseTool(agent_id=agent_id, api_key=embedding_api_key)
```

Note: `bind_tools_to_llm()` still uses the old signature (no embedding key) — it is called from paths that don't have per-user key context.

#### `backend/app/agent/custom_agent_runner.py`

**Change:** `run_custom_agent()` and `stream_custom_agent()` resolve the user's OpenAI key via `api_key_service` and pass it as `embedding_api_key` to `get_tools_list()`.

---

### B) Agent Chat Streaming Fixes (Frontend)

#### `frontend/src/components/agent-chat/AgentChatPage.tsx`

**Root Cause:**
After streaming ended, `invalidateQueries()` triggered a server refetch, causing a brief flicker as the optimistic user message disappeared and the server response loaded.

**Fix:**
On `event.type === 'end'`, the assistant message is written optimistically into the TanStack Query cache immediately. `invalidateQueries` is called with `refetchType: 'none'` so it marks the cache stale without an immediate network request:

```typescript
queryClient.setQueryData(
  ['conversation-messages', selectedConversationId],
  (old: AgentMessage[] = []) => [...old, assistantMessage]
)
queryClient.invalidateQueries({
  queryKey: ['conversation-messages', selectedConversationId],
  refetchType: 'none',
})
```

#### `frontend/src/components/agent-chat/MessageList.tsx`

**Root Cause:**
The streaming bubble previously used a blinking cursor span (`::after` pseudo-element) that was mispositioned when text wrapped, and a simple border that didn't visually indicate active streaming.

**Fix:**
Replaced cursor span with a `animate-streaming-border` wrapper div that applies a rotating conic-gradient border. The `StreamingMessageBubble` wraps content in:

```tsx
<div className="animate-streaming-border p-[1px] rounded-lg">
  <div className="rounded-lg px-4 py-3 bg-card text-foreground">
    {/* content */}
  </div>
</div>
```

#### `frontend/src/index.css`

**Change:** Added `@keyframes streaming-border-spin` and `animate-streaming-border` utility class:

```css
@keyframes streaming-border-spin {
  from { --streaming-angle: 0deg; }
  to   { --streaming-angle: 360deg; }
}

.animate-streaming-border {
  background: conic-gradient(
    from var(--streaming-angle, 0deg),
    transparent 0deg,
    hsl(var(--primary)) 60deg,
    transparent 120deg
  );
  animation: streaming-border-spin 2s linear infinite;
}
```

Uses CSS `@property` for `--streaming-angle` to enable smooth animation of the custom property.

---

## 🗂 Files Changed

| File | Type | Change |
|------|------|--------|
| `backend/app/api/routes/models.py` | Backend | Per-user Redis cache key |
| `backend/app/services/model_discovery.py` | Backend | Extended OpenAI fallback list + per-user key forwarding |
| `backend/app/agent/tools/knowledge_base_tool.py` | Backend | `api_key` field for per-user embedding |
| `backend/app/agent/tools/tool_registry.py` | Backend | `embedding_api_key` param in `get_tools_list()` |
| `backend/app/agent/custom_agent_runner.py` | Backend | Resolve + forward per-user OpenAI key |
| `frontend/src/components/agent-chat/AgentChatPage.tsx` | Frontend | Optimistic assistant message on stream end |
| `frontend/src/components/agent-chat/MessageList.tsx` | Frontend | Conic-gradient border streaming indicator |
| `frontend/src/index.css` | Frontend | `animate-streaming-border` keyframes |
