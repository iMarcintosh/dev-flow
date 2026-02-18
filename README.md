# DevFlow 🚀

**AI-Powered Development Workspace** - A comprehensive platform combining project management, intelligent automation, and collaborative AI agents.

DevFlow transforms your development workflow with Kanban boards, custom AI agents, team collaboration, and advanced features like code execution, knowledge bases, and real-time analytics.

---

## ✨ Features

### 🎯 Project Management
- **Kanban Boards** - Drag-and-drop task management with customizable columns
- **Board Integration** - Direct agent assignment and interaction on tasks
- **Project Organization** - Multi-project support with team access control

### 🤖 Custom AI Agents
- **Agent Hub** - Create and manage custom AI agents with specific roles
  - **Modern Card UI** - Icon-based stats, elegant diagonal shine hover effect
  - **Scheduled Agents** - Run agents automatically on cron schedules (hourly, daily, weekly, custom)
  - **Agent Details Modal** - Comprehensive analytics, tool usage, and execution history
- **Model Selection** - Choose from Claude, GPT-4, and other LLMs
- **Tool Integration** - Equip agents with powerful capabilities:
  - 📋 **Board Management** - Create and update tasks
  - 🔍 **Web Search** - Find up-to-date information
  - 💻 **Code Execution** - Run Python, JavaScript, Bash in isolated Docker containers
  - 📚 **Knowledge Base** - RAG with semantic search through uploaded documents
- **Configurable Parameters** - Temperature, max tokens, system prompts
- **Public/Private/Team** - Flexible visibility and sharing options

### 📚 Knowledge Base (RAG)
- **File Upload** - PDF, Markdown, TXT, code files
- **Local Embeddings** - No OpenAI API required! Uses sentence-transformers
- **Vector Search** - ChromaDB with semantic similarity
- **Automatic Chunking** - Smart text splitting with overlap
- **Drag & Drop UI** - Easy file management in agent modal

### 💬 Agent Chat
- **WebSocket Streaming** - Real-time token-by-token responses
- **Conversation Management** - Multiple conversations per agent
- **Context-Aware** - Agents access project and task context
- **Tool Execution** - Agents can use enabled tools during chat

### 🐳 Docker Code Execution
- **Secure Sandboxing** - Isolated container execution
- **Multi-Language** - Python 3.11, Node.js 20, Bash/Alpine
- **Resource Limits** - CPU (50%), Memory (128MB), timeout protection
- **Network Isolation** - No external network access
- **Auto Image Pulling** - Handles required Docker images automatically

### 👥 Team Management
- **Team Creation** - Organize users into collaborative teams
- **Role-Based Access** - Owner, Admin, Member permissions
- **Member Management** - Invite, remove, update roles
- **Team Agents** - Share agents across team members

### 📊 Usage Analytics
- **Automatic Tracking** - Every agent run is logged with detailed metrics
- **Performance Metrics** - Response times (min/max/avg), success rates
- **Token Tracking** - Accurate token counting with tiktoken (prompt + completion tokens)
- **Tool Statistics** - Track which tools are used most with success rates
- **Scheduled Run History** - View complete execution logs for scheduled agents
- **Daily Aggregation** - Efficient time-series data
- **Per-Agent & Global** - Analyze individual agents or overall usage
- **Visibility-Based Access** - Private agents show only owner data, public/team aggregate all users
- **REST API** - Comprehensive endpoints for querying analytics and execution history

### 🔐 Security & API Keys
- **Per-User API Keys** - Store your own Anthropic, OpenAI, OpenRouter keys
- **Encryption** - All API keys encrypted at rest
- **Key Management UI** - Easy setup and testing
- **Model Configuration** - Configure available models per user

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/iMarcintosh/dev-flow.git
cd dev-flow

# Start the entire stack
docker-compose up -d

# Wait for services to be ready (~30 seconds)
# Check health: curl http://localhost:8000/health
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### First Steps

1. **Register** - Create an account at http://localhost:5173/register
2. **Add API Keys** - Go to Settings → API Keys and add your LLM provider keys
3. **Create an Agent** - Visit Agent Hub and create your first custom agent
4. **Upload Knowledge** - (Optional) Add documents to your agent's knowledge base
5. **Start Chatting** - Open the agent and start a conversation!

---

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TanStack Router (routing)
- TanStack Query (data fetching)
- Tailwind CSS (styling)
- DND Kit (drag & drop)
- Lucide Icons

**Backend:**
- FastAPI (API framework)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL + pgvector (database)
- Alembic (migrations)
- LangChain (agent framework)
- ChromaDB (vector store)
- Docker SDK (code execution)

**Background Jobs:**
- Celery (task queue)
- Redis (message broker)
- Celery Beat (scheduling)

**AI/ML:**
- Anthropic Claude (LLM)
- OpenAI GPT (LLM)
- OpenRouter (multi-provider)
- sentence-transformers (local embeddings)

### System Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React App     │─────▶│   FastAPI        │─────▶│   PostgreSQL    │
│   (Frontend)    │      │   (Backend)      │      │   + pgvector    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                │
                                ├──────────▶ ChromaDB (Vectors)
                                │
                                ├──────────▶ Docker Engine (Code Exec)
                                │
                                └──────────▶ Redis (Cache + Queue)
                                                 │
                                                 ▼
                                            Celery Workers
```

---

## 📚 API Documentation

### Interactive Docs
Visit http://localhost:8000/docs for full interactive API documentation (Swagger UI).

### Key Endpoints

**Authentication:**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/refresh` - Refresh access token

**Custom Agents:**
- `GET /api/custom-agents` - List user's agents
- `POST /api/custom-agents` - Create new agent
- `GET /api/custom-agents/{id}` - Get agent details
- `PATCH /api/custom-agents/{id}` - Update agent
- `DELETE /api/custom-agents/{id}` - Delete agent

**Knowledge Base:**
- `POST /api/knowledge-base/{agent_id}/upload` - Upload file
- `GET /api/knowledge-base/{agent_id}/files` - List files
- `DELETE /api/knowledge-base/{agent_id}/files/{file_id}` - Delete file
- `POST /api/knowledge-base/{agent_id}/search` - Search knowledge base

**Analytics:**
- `GET /api/analytics/agents/{agent_id}/summary` - Agent summary stats
- `GET /api/analytics/agents/{agent_id}` - Timeline data
- `GET /api/analytics/agents/{agent_id}/tools` - Tool usage stats
- `GET /api/analytics/summary` - Global user summary
- `GET /api/analytics/tools` - Global tool usage

**Teams:**
- `GET /api/teams` - List user's teams
- `POST /api/teams` - Create team
- `GET /api/teams/{id}` - Get team details
- `POST /api/teams/{id}/members` - Add member
- `PATCH /api/teams/{id}/members/{user_id}` - Update member role
- `DELETE /api/teams/{id}/members/{user_id}` - Remove member

**WebSocket:**
- `WS /ws/agent-chat/{agent_id}?token={jwt}` - Real-time agent chat

---

## 🛠️ Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Format code
black app/
isort app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with API URL

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show current version
alembic current
```

---

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
# Database
DATABASE_URL=postgresql+asyncpg://devflow:devflow@localhost:5432/devflow

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (optional)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# LLM API Keys (optional - can be set per-user in UI)
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here

# Docker (for code execution)
DOCKER_HOST=unix:///var/run/docker.sock
```

**Frontend (.env):**
```env
VITE_API_URL=http://localhost:8000
```

### Docker Compose Services

```yaml
services:
  postgres:    # PostgreSQL with pgvector
  redis:       # Redis for caching and Celery
  backend:     # FastAPI application
  frontend:    # React/Vite dev server
  celery_worker:  # Background task worker
  celery_beat:    # Scheduled task runner
```

---

## 📖 Usage Guide

### Creating a Custom Agent

1. Navigate to **Agent Hub** (`/agents`)
2. Click **"Create Agent"**
3. Configure:
   - **Name**: e.g., "Code Review Assistant"
   - **Icon**: Choose an emoji (e.g., 🔍)
   - **Model**: Select from available LLMs
   - **System Prompt**: Define agent's role and capabilities
   - **Tools**: Enable code_execution, knowledge_base, etc.
   - **Parameters**: Temperature (creativity), Max tokens (length)
   - **Visibility**: Private, Team, or Public
4. Click **"Create Agent"**

### Adding Knowledge to an Agent

1. Open your agent in Agent Hub
2. Click **"Edit"** (pencil icon)
3. Switch to **"Knowledge Base"** tab
4. Drag & drop files or click to upload
5. Supported: PDF, TXT, MD, PY, JS, TS, JSON, YAML
6. Files are automatically chunked and embedded
7. Agent can now search this knowledge during conversations

### Using Code Execution

Agents with `code_execution` tool can run code:

**Example prompt:**
> "Write a Python script to calculate fibonacci numbers and run it for n=10"

The agent will:
1. Write the Python code
2. Execute it in a sandboxed Docker container
3. Return the output

**Security:**
- No network access
- 128MB memory limit
- 50% CPU limit
- 30-second timeout
- Read-only filesystem

### Team Collaboration

1. Go to **Teams** (`/teams`)
2. Click **"Create Team"**
3. Add members by email (must be registered users)
4. Assign roles:
   - **Owner**: Full control
   - **Admin**: Manage members and settings
   - **Member**: View and contribute
5. Share agents with team by setting visibility to "Team"

### Analytics & Monitoring

View agent performance:
1. Go to Agent Hub
2. Click on an agent
3. Select **"Analytics"** tab (if implemented in UI)

Or use API endpoints:
```bash
# Get summary
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/agents/{agent_id}/summary

# Get tool usage
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/agents/{agent_id}/tools
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Unit tests (if configured)
npm test

# E2E tests (if configured)
npm run test:e2e
```

### Manual Testing

See [TESTING-GUIDE.md](TESTING-GUIDE.md) for comprehensive manual testing procedures.

---

## 📦 Deployment

### Production Build

**Backend:**
```bash
cd backend
docker build -t devflow-backend .
```

**Frontend:**
```bash
cd frontend
npm run build
# Outputs to dist/ folder
```

### Environment Considerations

- Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- Set `CORS_ORIGINS` to your production domain
- Use managed PostgreSQL and Redis in production
- Enable HTTPS/SSL
- Set up proper logging and monitoring
- Configure backup strategies for PostgreSQL
- Use environment-specific configurations

---

## 🐛 Troubleshooting

### Common Issues

**1. Docker socket permission denied**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Restart shell or system
```

**2. Database connection errors**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**3. Frontend can't connect to backend**
```bash
# Check VITE_API_URL in frontend/.env
# Should be http://localhost:8000

# Check CORS_ORIGINS in backend/.env
# Should include http://localhost:5173
```

**4. Knowledge base embeddings not working**
```bash
# Check if sentence-transformers is installed
docker exec devflow-backend pip list | grep sentence

# Reinstall if needed
docker exec devflow-backend pip install sentence-transformers==2.3.1
```

**5. Code execution fails**
```bash
# Check Docker socket is mounted
docker-compose exec backend ls -la /var/run/docker.sock

# Check backend user is in docker group
docker-compose exec backend groups

# Rebuild backend with correct GID
docker-compose build backend
```

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with descriptive messages
6. Push to your fork
7. Open a Pull Request

### Code Style

- **Python**: Black formatter, isort for imports, PEP 8
- **TypeScript**: Prettier, ESLint
- **Commits**: Conventional Commits format

### Areas for Contribution

- 🎨 UI/UX improvements
- 📊 Analytics dashboard frontend
- 🔌 New agent tools
- 🧪 Test coverage
- 📖 Documentation
- 🌍 Internationalization
- ♿ Accessibility improvements

---

## 📄 License

Proprietary - All rights reserved

---

## 🙏 Acknowledgments

- **LangChain** - Agent framework
- **FastAPI** - Backend framework
- **React** - Frontend library
- **Anthropic** - Claude LLM
- **OpenAI** - GPT models
- **ChromaDB** - Vector database
- **sentence-transformers** - Local embeddings

---

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Testing Guide**: [TESTING-GUIDE.md](TESTING-GUIDE.md)

---

## 🗺️ Roadmap

### Completed ✅
- ✅ Authentication & User Management
- ✅ Kanban Boards with Drag & Drop
- ✅ Custom AI Agents
- ✅ Agent Tools (Board, Search, Code, Knowledge Base)
- ✅ Team Management
- ✅ Docker Code Execution
- ✅ Knowledge Base with RAG
- ✅ WebSocket Streaming
- ✅ Usage Analytics
- ✅ Per-User API Keys

### In Progress 🚧
- 🚧 Analytics Dashboard UI
- 🚧 WebSocket Chat Integration (Frontend)

### Planned 📋
- 📋 Agent Marketplace
- 📋 Workflow Automation
- 📋 Advanced Scheduling
- 📋 Multi-modal Support (Images, Audio)
- 📋 Plugin System
- 📋 Mobile App

---

**Made with ❤️ using AI assistance**

---

## 🎨 Recent Updates

### Agent Hub UI Improvements (2026-02-18)
- **Modern Card Design** - Icon-based statistics without text labels for cleaner look
- **Diagonal Shine Effect** - Elegant hover animation with 400ms delay and soft blur
- **Fixed Layout** - Consistent 420px card height with flex layout
- **Enhanced UX** - Action buttons in top-right, chat button always at bottom
- **Token Tracking** - Accurate token counting for scheduled agents using tiktoken
- **Scheduled Runs UI** - Complete execution history with expandable details
- **Better Analytics** - Visibility-based access control and detailed breakdowns

### Scheduled Agents (2026-02-17)
- **Cron Scheduling** - Run agents automatically on custom schedules
- **Preset Schedules** - Hourly, daily, weekly, monthly, weekdays presets
- **Next Run Preview** - See when agent will execute next
- **Manual Trigger** - Run scheduled agents on-demand
- **Execution History** - Track all scheduled runs with status and logs

### Custom Agent Tools (2026-02-16)
- **Knowledge Base** - RAG with local embeddings, no OpenAI required
- **Code Execution** - Python, JavaScript, Bash in secure Docker containers
- **Web Search** - Real-time web search for up-to-date information
- **Board Integration** - Create and manage tasks from agents

