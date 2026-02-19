# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DevFlow is an AI-powered development workspace combining Kanban project management with custom AI agents, real-time chat, code execution, and knowledge bases. It's a full-stack monorepo with a FastAPI backend and React frontend, deployed via Docker Compose.

## Commands

### Docker Compose (recommended for full stack)

```bash
docker compose up               # Start all 6 services
docker compose up --build       # Start with rebuild
docker compose down             # Stop services
docker compose logs -f backend  # Watch service logs
docker compose exec backend bash # Enter container shell
```

### Backend (standalone)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
celery -A app.celery_app worker --loglevel=info  # Worker
celery -A app.celery_app beat --loglevel=info    # Scheduler
```

### Frontend (standalone)

```bash
cd frontend
npm run dev          # Dev server with HMR (port 5173)
npm run build        # Production build (tsc + vite)
npm run type-check   # TypeScript validation
npm run lint         # ESLint
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"  # Create
alembic upgrade head                               # Apply
alembic downgrade -1                               # Rollback
alembic current                                    # Check version
```

### Testing

```bash
# Backend
cd backend
pytest
pytest tests/test_agents.py::test_task_creator_agent -v  # Single test
pytest --cov=app                                          # With coverage

# Frontend
cd frontend
npm test
npm test -- TaskCard.test.tsx  # Single test
```

### Code Quality

```bash
cd backend
black app/   # Format Python
isort app/   # Sort imports
```

## Architecture

### Services (Docker Compose)

| Service | Port | Purpose |
|---------|------|---------|
| frontend | 5173 | React/Vite dev server |
| backend | 8000 | FastAPI + Uvicorn |
| postgres | 5432 | PostgreSQL with pgvector extension |
| redis | 6379 | Celery broker + cache |
| celery_worker | — | Background task processing |
| celery_beat | — | Cron-based scheduled agents |

API docs at http://localhost:8000/docs. WebSocket at `ws://localhost:8000/ws/agent-chat/{agent_id}?token={jwt}`.

### Backend Structure (`backend/app/`)

- **`agent/`** — Agent framework (LangChain/LangGraph)
  - `base_agent.py` — Abstract base class with `run()`, `log()`, `trigger` type
  - `registry.py` — Singleton `AgentRegistry` (agents self-register at module level)
  - `scheduler.py` — Reads registry on startup, adds cron tasks to Celery Beat
  - `custom_agent_runner.py` — Async execution with WebSocket streaming
  - `agents/` — Concrete agent implementations
  - `tools/` — LangChain `BaseTool` implementations (web, code, board, knowledge base, weather)
  - `memory/indexer.py` — Celery tasks for async vector embedding
- **`api/routes/`** — 16 FastAPI routers (auth, projects, items, custom-agents, knowledge-base, analytics, teams, api-keys, websocket, etc.)
- **`models/`** — SQLAlchemy 2.0 async ORM models
- **`schemas/`** — Pydantic v2 validation schemas
- **`services/`** — Business logic (agent execution, knowledge base RAG, code execution sandbox, API key encryption, analytics)
- **`celery_app.py`** — Celery configuration
- **`auth.py`** — JWT authentication
- **`config.py`** — Environment configuration via Pydantic Settings

### Frontend Structure (`frontend/src/`)

- **`components/`** — Organized by feature: `board/`, `agent-hub/`, `agent-chat/`, `cards/`, `auth/`, `settings/`, `teams/`, `admin/`, `ui/`
- **`services/`** — `api.ts` (Axios client), `websocket.ts`, `queries.ts` (TanStack Query hooks), `custom-agents.ts`, `knowledgeBase.ts`, etc.
- **`stores/`** — Zustand stores for client state
- **`types/`** — TypeScript interfaces
- **`hooks/`** — Custom React hooks

### Agent System

Agents self-register at module level:
```python
registry.register(MyAgent())
```

The 3-phase tool-calling workflow: **plan → execute → respond**. Custom agents have two prompt fields:
- `system_prompt` — Agent behavior and role definition
- `scheduled_prompt` — Actual question/task used during cron runs

Trigger types: `manual`, `scheduled` (note: `chat` trigger was removed in iteration 6).

### Key Patterns

**Position field for Kanban ordering** — Items use float positions, midpoint insertion: `(prev + next) / 2`. Recalculate all after ~50 reorders.

**Optimistic UI updates** — DnD operations update locally first, then call API with rollback on error.

**Per-user encrypted API keys** — LLM API keys stored encrypted in DB; users configure keys in Settings UI or via backend `.env` (fallback).

**WebSocket event types:**
```typescript
{ type: "agent_log", run_id, level, message, timestamp }
{ type: "agent_status", agent_name, status, run_id }
{ type: "agent_finished", run_id, result }
```

**Board columns** — Fixed: `backlog | in_progress | review | done`

**Item types** — `epic | story | bug | task | spike`

**pgvector** — First migration must `CREATE EXTENSION IF NOT EXISTS vector`. Embeddings use local `sentence-transformers` (no OpenAI key needed). SQLAlchemy event listeners auto-trigger Celery embedding tasks on item changes.

**Code execution** — Docker SDK runs sandboxed containers (Python 3.11, Node.js 20, Bash). No network access, 128MB RAM, 50% CPU, 30s timeout.

### Frontend Design Conventions

- Dark mode by default (Linear/Vercel aesthetic)
- Geist/Geist Mono fonts (not Inter/Roboto)
- Status colors: Backlog=gray, In Progress=blue, Review=orange, Done=green
- Micro-interactions with hover states and loading skeletons

### API Response Patterns

```python
{"success": true, "data": {...}}   # Success
{"success": false, "error": "...", "details": {...}}  # Error
```

## Environment Variables

**Backend (`backend/.env`):**
```env
DATABASE_URL=postgresql+asyncpg://devflow:devflow@postgres:5432/devflow
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
# Optional (can be set per-user in UI):
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Frontend (`frontend/.env`):**
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Initial Setup (New Machine)

After `docker compose up -d`, run:

```bash
./scripts/setup-dev.sh
```

This applies all DB migrations and creates the test user. Idempotent — safe to run multiple times.

**Test credentials:**
- Email: `test@devflow.dev`
- Password: `test1234`

## Important Notes

- The `chromadb/` data directory is tracked by git but should generally be excluded from commits
- Axios interceptor auto-refreshes JWT before expiry — no manual token management needed in frontend code
- Weather tool uses Open-Meteo (free, no API key) — do not revert to OpenWeather
- `DOCKER_HOST=unix:///var/run/docker.sock` must be mounted for code execution to work
