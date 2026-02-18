# DevFlow – Copilot Instructions

AI-powered Developer Workspace with Kanban boards, agent system, and chat.

## Tech Stack

### Frontend
- **React 18 + TypeScript + Vite**
- **Tailwind CSS + shadcn/ui** (dark mode default)
- **@dnd-kit** for drag & drop
- **Zustand** for local state, **TanStack Query** for server state
- **TanStack Router** for routing
- **Native WebSocket** for live agent status

### Backend
- **FastAPI** (Python 3.11+)
- **SQLAlchemy 2.0 + Alembic** for ORM + migrations
- **PostgreSQL with pgvector** for embeddings
- **Redis** for Celery broker + cache
- **Celery + Celery Beat** for async tasks + scheduling
- **FastAPI Users** for auth, **Authlib** for OAuth2
- **LangChain + LangGraph** for agent orchestration

### Infrastructure
- **Docker Compose** for local development
- Services: `frontend`, `backend`, `postgres`, `redis`, `celery_worker`, `celery_beat`

## Build & Run Commands

### Start entire stack
```bash
docker compose up
```

### Start with rebuild
```bash
docker compose up --build
```

### Backend only (for development)
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend only (for development)
```bash
cd frontend
npm run dev
```

### Run Celery worker manually
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

### Run Celery beat manually
```bash
cd backend
celery -A app.celery_app beat --loglevel=info
```

## Database Migrations

### Create new migration
```bash
cd backend
alembic revision --autogenerate -m "description"
```

### Apply migrations
```bash
cd backend
alembic upgrade head
```

### Rollback one migration
```bash
cd backend
alembic downgrade -1
```

## Testing

### Backend tests
```bash
cd backend
pytest
```

### Backend single test
```bash
cd backend
pytest tests/test_agents.py::test_task_creator_agent -v
```

### Frontend tests
```bash
cd frontend
npm test
```

### Frontend single test
```bash
cd frontend
npm test -- TaskCard.test.tsx
```

## Architecture

### Agent System Core Concept
- **Registry Pattern**: All agents self-register via singleton `AgentRegistry`
- **Base Agent**: Abstract class defining `run()`, `log()`, and `trigger` type
- **LangGraph Orchestration**: Agents define node chains for multi-step workflows
- **Live Streaming**: WebSocket pushes logs to frontend in real-time
- **Tool System**: LangChain-compatible tools inherit from `BaseTool`

### Agent Types & Triggers
- **MANUAL**: User-initiated via UI button
- **CHAT**: Triggered by chatbot conversation
- **EVENT**: Database events (e.g., item created)
- **SCHEDULED**: Cron-based via Celery Beat
- **WEBHOOK**: External API calls

### Memory & Context
- **pgvector**: Embeddings stored in PostgreSQL vector column
- **Auto-indexing**: SQLAlchemy events trigger Celery tasks on item changes
- **Retrieval**: Chat agent uses semantic search to find relevant items
- **Embedding format**: `f"{type}: {title}\n{description}\n{acceptance_criteria}"`

### WebSocket Event Types
```typescript
// Agent log streaming
{ type: "agent_log", run_id, level, message, timestamp }

// Agent status updates
{ type: "agent_status", agent_name, status, run_id }

// Agent completion
{ type: "agent_finished", run_id, result }
```

### Database Models Hierarchy
- **User** → owns **Projects**
- **Project** → contains **Items**
- **Item** → can have parent (for epics/subtasks)
- **AgentRun** → belongs to **User**, references **Project**
- **ChatMessage** → belongs to **User** + **Project**, optionally links to **AgentRun**

## Key Conventions

### Position Field for Drag & Drop
Items use a `position` float field for ordering within columns:
- On reorder: `position = (prev_position + next_position) / 2`
- After ~50 reorders: recalculate all positions in column (1.0, 2.0, 3.0...)

### Optimistic Updates
Frontend DnD operations update UI immediately, then call API:
```typescript
// Optimistic update
updateItemLocally(item);
// API call
try {
  await updateItem(item);
} catch {
  rollbackItem(item); // Revert on error
}
```

### Agent Registration
All agents auto-register on import:
```python
class MyAgent(BaseDevFlowAgent):
    name = "my_agent"
    # ...

registry.register(MyAgent())  # At module level
```

### Scheduled Agent Setup
`scheduler.py` reads registry on app startup and dynamically adds to Celery Beat:
```python
for agent in registry.scheduled():
    celery_app.add_periodic_task(
        crontab(**parse_cron(agent.schedule)),
        run_agent.s(agent.name)
    )
```

### Tool Structure
All custom tools inherit from LangChain's `BaseTool`:
```python
class CreateItemTool(BaseTool):
    name = "create_item"
    description = "Creates a new board item"
    
    def _run(self, **kwargs):
        # Implementation
```

### Embedding Triggers
SQLAlchemy event listeners auto-trigger embedding updates:
```python
@event.listens_for(Item, 'after_insert')
def item_inserted(mapper, connection, target):
    index_item.delay(target.id)  # Celery task
```

### Error Handling in Agents
All agent errors are logged and streamed:
```python
try:
    result = await self.run(input, run_id)
except Exception as e:
    await self.log(run_id, str(e), level="error")
    await update_run_status(run_id, "failed", error=str(e))
    raise
```

### Frontend Design Language
- **Dark mode by default** (Linear/Vercel style)
- **Geist/Geist Mono fonts** (not Inter/Roboto)
- **Status colors**: Backlog=gray, In Progress=blue, Review=orange, Done=green
- **Priority indicators**: Color-coded dots/icons
- **Micro-interactions**: Hover states, smooth animations, loading skeletons

### API Response Patterns
```python
# Success
{"success": true, "data": {...}}

# Error
{"success": false, "error": "message", "details": {...}}

# Agent preview (before import)
{
  "run_id": "...",
  "preview": [
    {"type": "story", "title": "...", "description": "..."}
  ]
}
```

### WebSocket Connection Management
Backend maintains `ConnectionManager` singleton:
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def broadcast_to_run(self, run_id: str, message: dict):
        # Send to all clients watching this run
```

## Environment Variables

Required in `.env`:
```env
# Database
DATABASE_URL=postgresql+asyncpg://devflow:devflow@postgres:5432/devflow

# Redis
REDIS_URL=redis://redis:6379

# JWT
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# LLM
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
LLM_PROVIDER=anthropic

# SMTP
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM=noreply@devflow.dev
```

## Project Structure

```
devflow/
├── frontend/src/
│   ├── components/
│   │   ├── board/           # Kanban with 4 columns
│   │   ├── cards/           # Item cards + detail modals
│   │   ├── chatbot/         # Bottom-right chat widget
│   │   ├── agent-hub/       # Agent dashboard
│   │   └── auth/            # Login/register
│   ├── stores/              # Zustand stores
│   ├── services/
│   │   ├── api.ts           # Axios client
│   │   └── websocket.ts     # WS service
│   └── router.tsx           # TanStack Router
│
├── backend/app/
│   ├── api/routes/          # FastAPI endpoints
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/
│   │   └── embedding_service.py
│   └── agent/
│       ├── base_agent.py    # Abstract base
│       ├── registry.py      # Agent registry
│       ├── scheduler.py     # Celery Beat integration
│       ├── graph.py         # LangGraph orchestrator
│       ├── agents/          # Concrete agents
│       ├── memory/          # Vector store + indexer
│       └── tools/           # LangChain tools
│
└── alembic/                 # Migrations
```

## Important Implementation Notes

1. **pgvector Extension**: First migration must enable it:
   ```python
   op.execute('CREATE EXTENSION IF NOT EXISTS vector')
   ```

2. **Token Refresh**: Axios interceptor auto-refreshes JWT before expiry

3. **Item Types**: epic | story | bug | task | spike (with distinct visual styling)

4. **Board Columns**: backlog | in_progress | review | done (fixed, not customizable)

5. **Agent Preview Flow**: Run → Generate → Preview → User confirms → Import to DB

6. **Chat Streaming**: Use Server-Sent Events (SSE) for streaming responses

7. **Item References in Chat**: Parse `[ITEM-123]` syntax and render as clickable chips

8. **Markdown Support**: Item descriptions use markdown (preview + edit modes)

9. **Quality Standards**: Production-ready code with proper error handling, TypeScript types, Pydantic schemas
