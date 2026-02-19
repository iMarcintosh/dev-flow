# DevFlow - Development Setup Guide

**Platform:** macOS (works on Linux/Windows too)  
**Last Updated:** 2026-02-19

This guide will help you set up DevFlow on a new machine for development.

---

## 📋 Prerequisites

### Required Software

1. **Docker Desktop**
   ```bash
   # Install from: https://www.docker.com/products/docker-desktop
   # Or via Homebrew:
   brew install --cask docker
   
   # Verify installation
   docker --version
   docker compose version
   ```

2. **Git**
   ```bash
   # Usually pre-installed on macOS
   git --version
   
   # If not installed:
   brew install git
   ```

3. **Node.js** (v18+ recommended)
   ```bash
   # Via Homebrew:
   brew install node
   
   # Verify installation
   node --version
   npm --version
   ```

4. **Python** (3.11+ for local development, optional)
   ```bash
   # Via Homebrew:
   brew install python@3.11
   
   # Verify installation
   python3 --version
   ```

5. **Text Editor / IDE**
   - VS Code (recommended): https://code.visualstudio.com
   - Or your preferred editor

---

## 🚀 Initial Setup

### Step 1: Clone Repository

```bash
# Navigate to your projects directory
cd ~/Projects  # or wherever you keep projects

# Clone the repository
git clone https://github.com/iMarcintosh/dev-flow.git
cd dev-flow

# Check current branch
git branch
# Should show: * main
```

### Step 2: Environment Variables

Create `.env` file in the `backend` directory:

```bash
cd backend
cp .env.example .env  # If .env.example exists
# OR create manually:
```

**Edit `backend/.env`:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://devflow:devflow@postgres:5432/devflow

# Redis
REDIS_URL=redis://redis:6379

# JWT Secret (CHANGE THIS!)
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# LLM API Keys (Get from providers)
OPENAI_API_KEY=sk-...  # Optional: Get from https://platform.openai.com
ANTHROPIC_API_KEY=sk-ant-...  # Optional: Get from https://console.anthropic.com

# Default LLM Provider
LLM_PROVIDER=anthropic  # or 'openai'

# OAuth (Optional - for social login)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Email (Optional - for notifications)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM=noreply@devflow.dev

# Environment
ENVIRONMENT=development
DEBUG=true
```

**⚠️ Important:** Change `SECRET_KEY` to a random string:
```bash
# Generate a secure secret key:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Start Docker Services

```bash
# Return to project root
cd ..

# Start all services
docker compose up -d

# Check status
docker compose ps
```

**Expected output:**
```
NAME                     STATUS       PORTS
devflow-backend          running      0.0.0.0:8000->8000/tcp
devflow-celery-beat      running
devflow-celery-worker    running
devflow-frontend         running      0.0.0.0:5173->5173/tcp
devflow-postgres         running      0.0.0.0:5432->5432/tcp
devflow-redis            running      0.0.0.0:6379->6379/tcp
```

**First time setup takes 5-10 minutes** (downloading images, building, migrations).

### Step 4: Wait for Services to Start

```bash
# Watch backend logs
docker compose logs -f backend

# Wait for this message:
# "Application startup complete."
# "Uvicorn running on http://0.0.0.0:8000"

# Press Ctrl+C to stop watching logs
```

### Step 5: Run Migrations and Create Test User

```bash
./scripts/setup-dev.sh
```

This script:
1. Runs all pending DB migrations (`alembic upgrade head`)
2. Creates the test user (skips silently if already exists)

**Test credentials:**
- Email: `test@devflow.dev`
- Password: `test1234`

---

## ✅ Verify Installation

### 1. Backend Health Check

```bash
# Check backend is running
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected"}
```

### 2. Frontend Access

Open browser and navigate to:
```
http://localhost:5173
```

**You should see:**
- DevFlow login page
- Dark mode interface
- Login form

### 3. Login Test

**Credentials:**
- Email: `test@devflow.dev`
- Password: `test1234`

**After login, you should see:**
- Empty Kanban board (4 columns: Backlog, In Progress, Review, Done)
- Navigation: Board, Agents, Chat
- Dark mode interface

### 4. Database Connection

```bash
# Connect to database
docker compose exec postgres psql -U devflow -d devflow

# Check tables
\dt

# Should list all tables:
# - users
# - projects
# - items
# - custom_agents
# - agent_runs
# - etc.

# Exit
\q
```

### 5. Celery Workers

```bash
# Check Celery worker logs
docker compose logs celery_worker --tail=20

# Should show:
# "celery@... ready."
# "mingle: all alone"

# Check Celery beat (scheduler)
docker compose logs celery_beat --tail=20

# Should show:
# "Scheduler: Sending due task..."
```

---

## 🛠️ Development Workflow

### Start Development

```bash
# Start all services
docker compose up -d

# Watch logs (all services)
docker compose logs -f

# Watch specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery_worker
```

### Stop Development

```bash
# Stop all services (keeps data)
docker compose down

# Stop and remove volumes (DESTROYS DATA!)
docker compose down -v
```

### Restart After Code Changes

**Backend (Python) changes:**
```bash
# Backend auto-reloads with watchfiles
# Just save the file, no restart needed

# If changes don't reflect:
docker compose restart backend
```

**Frontend (TypeScript/React) changes:**
```bash
# Frontend auto-reloads with Vite HMR
# Just save the file

# If changes don't reflect:
docker compose restart frontend
```

**Database schema changes:**
```bash
# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migration
docker compose exec backend alembic upgrade head

# Restart backend
docker compose restart backend
```

**Dependencies changed:**
```bash
# Backend: requirements.txt
docker compose build backend
docker compose up -d backend

# Frontend: package.json
docker compose build frontend
docker compose up -d frontend
```

### Access Services Directly

**Backend Shell:**
```bash
docker compose exec backend bash

# Inside container:
python
>>> from app.models.user import User
>>> # ... test code
```

**Database CLI:**
```bash
docker compose exec postgres psql -U devflow -d devflow

# SQL commands
SELECT * FROM users;
\dt  # List tables
\d users  # Describe table
\q  # Exit
```

**Redis CLI:**
```bash
docker compose exec redis redis-cli

# Redis commands
KEYS *
GET some_key
QUIT
```

---

## 🧪 Testing

### Run Backend Tests

```bash
# Unit tests
docker compose exec backend pytest

# With coverage
docker compose exec backend pytest --cov=app tests/

# Specific test file
docker compose exec backend pytest tests/test_agents.py -v
```

### Run Frontend Tests

```bash
# Unit tests
docker compose exec frontend npm test

# E2E tests (if configured)
docker compose exec frontend npm run test:e2e
```

### Manual API Testing

**Login and get token:**
```bash
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@devflow.dev","password":"test1234"}' \
  | jq -r '.access_token')

echo $TOKEN
```

**Create a project:**
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","description":"My first project"}'
```

**List projects:**
```bash
curl http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check Docker Desktop is running
docker ps

# Check logs for errors
docker compose logs

# Rebuild everything
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find what's using the port
lsof -i :8000
lsof -i :5173

# Kill the process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres

# Check logs
docker compose logs postgres

# Reset database (DESTROYS DATA!)
docker compose down -v
docker compose up -d
```

### Migrations Out of Sync

```bash
# Check current migration
docker compose exec backend alembic current

# Check available migrations
docker compose exec backend alembic heads

# Downgrade one migration
docker compose exec backend alembic downgrade -1

# Upgrade to head
docker compose exec backend alembic upgrade head

# If completely broken, reset database:
docker compose down -v
docker compose up -d
docker compose exec backend alembic upgrade head
```

### Frontend Build Errors

```bash
# Clear node_modules and reinstall
docker compose exec frontend rm -rf node_modules package-lock.json
docker compose exec frontend npm install

# Or rebuild container
docker compose build frontend --no-cache
docker compose up -d frontend
```

### Celery Worker Not Running

```bash
# Check worker status
docker compose ps celery_worker

# Check logs
docker compose logs celery_worker

# Restart worker
docker compose restart celery_worker

# If still failing, rebuild:
docker compose build celery_worker
docker compose up -d celery_worker
```

### Out of Disk Space (macOS)

```bash
# Clean up Docker resources
docker system prune -a --volumes

# Warning: This removes ALL unused containers, images, volumes!
# Your dev-flow data will be preserved if containers are running
```

### Permission Errors (macOS)

```bash
# If you get permission errors, ensure Docker Desktop has:
# Settings → Resources → File Sharing
# Your project directory is listed

# Or fix permissions:
sudo chown -R $(whoami) .
```

---

## 📚 Useful Commands Cheat Sheet

```bash
# ===== Docker =====
docker compose up -d                    # Start all services
docker compose down                     # Stop all services
docker compose ps                       # List running services
docker compose logs -f [service]        # Watch logs
docker compose restart [service]        # Restart service
docker compose build [service]          # Rebuild service
docker compose exec [service] bash      # Enter container shell

# ===== Database =====
docker compose exec postgres psql -U devflow -d devflow
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "msg"
docker compose exec backend alembic current
docker compose exec backend alembic downgrade -1

# ===== Testing =====
docker compose exec backend pytest
docker compose exec backend pytest tests/test_agents.py -v
docker compose exec frontend npm test

# ===== Debugging =====
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose exec backend python  # Python REPL
docker compose exec backend bash    # Shell in backend

# ===== Cleanup =====
docker compose down -v              # Stop + remove volumes (DANGER!)
docker system prune -a              # Clean all unused Docker data
```

---

## 🎓 Next Steps After Setup

Once everything is running:

1. **Create Your First Project**
   - Navigate to http://localhost:5173
   - Login with test credentials
   - Click "New Project" or "+" button

2. **Create Custom Agent**
   - Go to "Agents" tab
   - Click "Create Agent"
   - Configure with tools (web_search, weather, etc.)
   - Test with manual execution

3. **Schedule an Agent**
   - Create agent with trigger="scheduled"
   - Set cron schedule (e.g., `*/5 * * * *` = every 5 minutes)
   - Add scheduled_prompt (e.g., "Wie ist das Wetter in Berlin?")
   - Watch logs: `docker compose logs -f celery_worker`

4. **Explore Analytics**
   - Go to agent detail view
   - Check "Analytics" tab
   - See run history, tool usage, performance

5. **Read Documentation**
   - [AGENT-GUIDE.md](./AGENT-GUIDE.md) - How to create agents
   - [TESTING-GUIDE.md](./TESTING-GUIDE.md) - Testing strategies
   - [ITERATION-6-STATUS.md](./ITERATION-6-STATUS.md) - Recent features

---

## 🔐 Security Notes

### For Development

- ✅ Use `.env` for secrets (never commit!)
- ✅ Use test credentials only
- ✅ Run on localhost only

### For Production

- ❌ Never use default SECRET_KEY
- ❌ Never expose database ports publicly
- ❌ Never commit API keys to git
- ✅ Use strong passwords
- ✅ Enable HTTPS
- ✅ Use production database (not SQLite)
- ✅ Configure CORS properly
- ✅ Use environment-specific .env files

---

## 📞 Support & Resources

### Documentation
- [README.md](./README.md) - Project overview
- [AGENT-GUIDE.md](./AGENT-GUIDE.md) - Agent development guide
- [TESTING-GUIDE.md](./TESTING-GUIDE.md) - Testing guide

### Common Issues
- Check [GitHub Issues](https://github.com/iMarcintosh/dev-flow/issues)
- Review [Checkpoints](./checkpoints/) for historical context

### Stack Documentation
- [FastAPI](https://fastapi.tiangolo.com)
- [React](https://react.dev)
- [LangChain](https://python.langchain.com)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Docker](https://docs.docker.com)

---

## ✅ Checklist for New Machine

- [ ] Install Docker Desktop
- [ ] Install Git, Node.js, Python
- [ ] Clone repository
- [ ] Create `backend/.env` file
- [ ] Set SECRET_KEY
- [ ] Add API keys (optional)
- [ ] Run `docker compose up -d`
- [ ] Wait for services to start (5-10 min first time)
- [ ] Run `./scripts/setup-dev.sh` (migrations + test user)
- [ ] Login at http://localhost:5173
- [ ] Create first project
- [ ] Create first agent
- [ ] Test scheduled agent
- [ ] Verify logs in `docker compose logs -f`

---

**Setup Complete!** 🎉

You're now ready to develop DevFlow on your new machine.

**Last Updated:** 2026-02-19  
**Platform:** macOS (also works on Linux/Windows with Docker Desktop)
