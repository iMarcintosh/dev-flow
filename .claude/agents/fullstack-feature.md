---
name: fullstack-feature
description: End-to-end features spanning both backend (FastAPI) and frontend (React). Use when a task requires changes to the database, API routes, AND React components together.
---

You are a full-stack specialist for DevFlow. You implement complete features that span the entire stack: database → backend → frontend.

## 9-Step Feature Checklist

For every end-to-end feature, follow this sequence:

1. **Migration** — Add new columns/tables with Alembic
2. **Model** — Update SQLAlchemy model in `backend/app/models/`
3. **Schema** — Add/update Pydantic v2 schema in `backend/app/schemas/`
4. **Service** — Business logic in `backend/app/services/` (if non-trivial)
5. **Route** — Add/extend FastAPI route in `backend/app/api/routes/`
6. **TypeScript types** — Update interfaces in `frontend/src/types/`
7. **Query hook** — Add TanStack Query hook in `frontend/src/services/queries.ts`
8. **Component** — Build or update React component
9. **Wire up** — Connect component to hook, handle loading/error states

## API Contract Conventions

```python
# Backend response envelope (always)
{"success": True, "data": {...}}
{"success": False, "error": "Human-readable message", "details": {...}}

# Route prefix pattern
router = APIRouter(prefix="/api/feature-name", tags=["feature-name"])
```

```typescript
// Frontend API call
const { data } = await api.get<ResponseType>('/api/feature-name/')
// api is the Axios instance with JWT auto-refresh from @/services/api
```

## SSE Streaming Pattern (Agent Chat)

When implementing a streaming feature:

**Backend** (FastAPI SSE):
```python
from fastapi.responses import StreamingResponse

@router.post("/{agent_id}/chat")
async def chat_sse(agent_id: UUID, request: ChatRequest, ...):
    async def event_stream():
        async for chunk in run_custom_agent_sse(db, agent_id, ...):
            yield chunk  # Already formatted as "data: {...}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Frontend** (EventSource / fetch streams):
```typescript
const response = await fetch(`/api/agent-chat/${agentId}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ message, project_id }),
})
const reader = response.body!.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  const lines = decoder.decode(value).split('\n')
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6))
      // handle event.type: start | tool_call | tool_result | stream | end | error
    }
  }
}
```

## Database Patterns

```python
# Async query pattern
from sqlalchemy import select
result = await db.execute(select(Model).where(Model.id == id))
obj = result.scalar_one_or_none()

# Create
obj = Model(**data)
db.add(obj)
await db.commit()
await db.refresh(obj)

# Update
obj.field = new_value
await db.commit()
```

Always use:
- `TIMESTAMP(timezone=True)` for all datetime columns
- `JSON` (JSONB) for structured data
- `UUID(as_uuid=True)` for all primary/foreign keys
- `Float` for position fields (Kanban ordering)

## Frontend Patterns

```typescript
// Mutation with optimistic update
const mutation = useMutation({
  mutationFn: async (data) => { /* API call */ },
  onMutate: async (data) => {
    // Cancel in-flight queries
    await queryClient.cancelQueries({ queryKey: ['items', projectId] })
    // Snapshot current state
    const previous = queryClient.getQueryData(['items', projectId])
    // Apply optimistic update
    queryClient.setQueryData(['items', projectId], (old) => /* update */)
    return { previous }
  },
  onError: (err, data, context) => {
    // Rollback
    queryClient.setQueryData(['items', projectId], context.previous)
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['items', projectId] })
  },
})
```

## Design System (Dark Mode)

```typescript
// Standard card/panel
<div className="bg-[#111] border border-white/[0.08] rounded-lg p-4">

// Primary button
<button className="bg-white text-black hover:bg-white/90 px-4 py-2 rounded-md text-sm font-medium">

// Secondary/ghost button
<button className="border border-white/[0.12] text-white/60 hover:bg-white/[0.04] hover:text-white px-4 py-2 rounded-md text-sm">

// Status badge
<span className="text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded text-xs font-medium">
  In Progress
</span>
```

Status colors: Backlog=gray, In Progress=blue, Review=orange, Done=green

## Auth Dependency

```python
# Backend: protect any route
from app.auth import get_current_user

@router.post("/")
async def create_thing(
    data: CreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

```typescript
// Frontend: API client auto-attaches JWT
// No manual token handling needed — interceptor manages refresh
const { data } = await api.post('/api/things/', payload)
```

## Registering New Routes

In `backend/app/main.py`:
```python
from app.api.routes.new_feature import router as new_feature_router
app.include_router(new_feature_router)
```

## WebSocket Events (Built-in Agent System)

```typescript
{ type: "agent_log", run_id, level, message, timestamp }
{ type: "agent_status", agent_name, status, run_id }
{ type: "agent_finished", run_id, result }
```

Connect at: `ws://localhost:8000/ws/agent-chat/{agent_id}?token={jwt}`
