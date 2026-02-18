# DevFlow

AI-powered Developer Workspace with Kanban boards, agent system, and chat.

## Quick Start

```bash
# Start entire stack
docker compose up

# Access the application
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

## Development

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## Architecture

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (pgvector)
- **Workers**: Celery + Redis
- **Agents**: LangChain + LangGraph

## Features (Roadmap)

- [x] **Iteration 1**: Auth system (email/password)
- [ ] **Iteration 2**: Kanban board with drag & drop
- [ ] **Iteration 3**: Agent system with task creator
- [ ] **Iteration 4**: Memory system + chatbot
- [ ] **Iteration 5**: Agent hub + scheduling

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `ANTHROPIC_API_KEY`: For LLM features (optional)

## License

Proprietary
