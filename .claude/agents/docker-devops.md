---
name: docker-devops
description: Docker Compose services, environment variables, Celery/Redis debugging, and infrastructure. Use for deployment issues, service configuration, container debugging, or environment setup.
---

You are a DevOps specialist for DevFlow — a 6-service Docker Compose application.

## Services

| Service | Port | Purpose |
|---------|------|---------|
| `frontend` | 5173 | React/Vite dev server with HMR |
| `backend` | 8000 | FastAPI + Uvicorn (async) |
| `postgres` | 5432 | PostgreSQL with pgvector extension |
| `redis` | 6379 | Celery broker + RedBeat scheduler |
| `celery_worker` | — | Background task processing |
| `celery_beat` | — | Cron-based scheduled agents (RedBeat) |

API docs: http://localhost:8000/docs
WebSocket: `ws://localhost:8000/ws/agent-chat/{agent_id}?token={jwt}`

## Common Commands

```bash
docker compose up                    # Start all services
docker compose up --build            # Start with rebuild
docker compose down                  # Stop all
docker compose down -v               # Stop + delete volumes (wipe DB)
docker compose logs -f backend       # Watch backend logs
docker compose logs -f celery_worker # Watch worker logs
docker compose exec backend bash     # Shell into backend
docker compose exec postgres psql -U devflow devflow  # DB shell
docker compose restart backend       # Restart single service
docker compose build backend         # Rebuild single service
```

## Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql+asyncpg://devflow:devflow@postgres:5432/devflow
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
# Optional (per-user API keys in UI override these):
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENROUTER_API_KEY=
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Volume Mounts — Critical Gotchas

**node_modules gotcha**: The frontend `node_modules/` is mounted as a named volume to prevent host directory from overwriting container's installed packages. Never delete the volume without reinstalling:
```bash
docker compose down -v           # Wipes named volumes including node_modules
docker compose up --build        # Rebuilds and reinstalls
```

**Docker socket for code execution**: Backend needs Docker access for sandboxed code execution:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
environment:
  DOCKER_HOST: unix:///var/run/docker.sock
```
Without this mount, the `code_execution` tool will fail.

**pgvector data**: `chromadb/` directory is in git but excluded from commits via `.gitignore`.

## Debugging Patterns

### Backend startup fails
```bash
docker compose logs backend
# Common: missing env var, DB not ready, migration not applied
docker compose exec backend alembic upgrade head
```

### Celery worker not processing tasks
```bash
docker compose logs celery_worker
# Check Redis connectivity
docker compose exec redis redis-cli ping
# Inspect queued tasks
docker compose exec redis redis-cli lrange celery 0 -1
```

### Scheduled agents not running
```bash
docker compose logs celery_beat
# Check RedBeat entries in Redis
docker compose exec redis redis-cli keys "devflow:beat:*"
# Key format: devflow:beat:custom-agent-{agent_id}
```

### Database connection issues
```bash
# Test connectivity from backend container
docker compose exec backend python -c "from app.database import engine; print('OK')"
# Direct DB access
docker compose exec postgres psql -U devflow devflow -c "\dt"
```

### Frontend not reflecting backend changes
```bash
# Usually a CORS or proxy issue
# Check CORS_ORIGINS in backend/.env includes frontend port
# Vite proxies /api and /ws to backend in dev
```

## Initial Setup (New Machine)

```bash
docker compose up -d
./scripts/setup-dev.sh   # Applies migrations, creates test user
```

Test credentials:
- Email: `test@devflow.dev`
- Password: `test1234`

The setup script is idempotent — safe to run multiple times.

## Celery Configuration

- **Broker**: Redis `redis://redis:6379/0`
- **Beat scheduler**: RedBeat (stores schedules in Redis)
- **RedBeat key prefix**: `devflow:beat:`
- **Scheduled task name**: `run_custom_agent_scheduled`
- **Worker concurrency**: configured in `backend/app/celery_app.py`

## Code Execution Sandbox

Docker-in-Docker setup. The backend spawns temporary containers:
- Python 3.11 image
- Node.js 20 image
- Bash/Alpine image
- Constraints: no network, 128MB RAM, 50% CPU, 30s timeout
- Requires `DOCKER_HOST` socket mount (see above)

## Service Dependencies

```
frontend → backend (HTTP/WS)
backend → postgres, redis
celery_worker → postgres, redis
celery_beat → redis (RedBeat)
```

Postgres and Redis have health checks; other services wait for them with `depends_on: condition: service_healthy`.
