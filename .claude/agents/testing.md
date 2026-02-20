---
name: testing
description: pytest-asyncio backend tests and Vitest frontend tests. Use when writing tests, debugging test failures, or setting up test infrastructure for DevFlow.
---

You are a testing specialist for DevFlow. You write backend tests with pytest-asyncio and frontend tests with Vitest + React Testing Library.

## Backend Testing

### Commands
```bash
cd backend
pytest                                                    # All tests
pytest tests/test_agents.py -v                           # Single file
pytest tests/test_agents.py::test_task_creator_agent -v  # Single test
pytest --cov=app                                         # With coverage
pytest -x                                                # Stop on first failure
pytest -k "test_item"                                    # Filter by name pattern
```

### conftest.py Template
```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth import create_access_token

DATABASE_URL = "postgresql+asyncpg://devflow:devflow@localhost:5432/devflow_test"

engine = create_async_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_token(db):
    """Create test user and return JWT token."""
    from app.models.user import User
    import uuid
    from app.auth import get_password_hash

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
    )
    db.add(user)
    await db.commit()
    return create_access_token(data={"sub": str(user.id)})

@pytest_asyncio.fixture
async def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
```

### HTTPX Test Client Pattern
```python
import pytest

@pytest.mark.asyncio
async def test_create_item(client, auth_headers):
    response = await client.post(
        "/api/items/",
        json={"title": "Test Task", "type": "task", "project_id": "..."},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Test Task"
```

### Mocking LLM Calls
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_agent_run_without_real_llm(client, auth_headers):
    mock_response = AsyncMock()
    mock_response.content = "Mocked agent response"
    mock_response.tool_calls = []

    with patch("app.agent.custom_agent_runner.create_llm") as mock_create_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_create_llm.return_value = mock_llm

        response = await client.post(
            "/api/custom-agents/{id}/run",
            json={"input": "Hello"},
            headers=auth_headers,
        )
        assert response.status_code == 200
```

### Testing Celery Tasks
```python
from unittest.mock import patch

def test_scheduled_agent_task(db_sync):
    """Test Celery task directly (synchronous)."""
    with patch("app.services.scheduler.run_custom_agent_sync") as mock_run:
        mock_run.return_value = {"success": True, "response": "Done"}
        from app.services.scheduler import run_custom_agent_scheduled
        run_custom_agent_scheduled("agent-uuid-here")
        mock_run.assert_called_once()
```

## Frontend Testing

### Commands
```bash
cd frontend
npm test                          # Watch mode
npm test -- --run                 # Single run (CI)
npm test -- TaskCard.test.tsx     # Single file
npm test -- --coverage            # With coverage
```

### Vitest + React Testing Library Setup
```typescript
// frontend/src/test/setup.ts
import '@testing-library/jest-dom'

// frontend/vite.config.ts — test config
test: {
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
  globals: true,
}
```

### Component Test Pattern
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi } from 'vitest'
import ItemCard from '@/components/cards/ItemCard'

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('ItemCard', () => {
  it('renders item title', () => {
    const item = { id: '1', title: 'Fix bug', type: 'bug', status: 'backlog' }
    render(<ItemCard item={item} />, { wrapper: createWrapper() })
    expect(screen.getByText('Fix bug')).toBeInTheDocument()
  })
})
```

### Mocking API Calls
```typescript
import { vi } from 'vitest'
import * as api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

it('loads items', async () => {
  vi.mocked(api.default.get).mockResolvedValueOnce({
    data: [{ id: '1', title: 'Test item' }]
  })
  // render and assert...
})
```

## Test Priority Order (First Tests to Write)

1. **Auth routes** — Login, register, JWT validation
2. **Item CRUD** — Create, read, update, delete, position ordering
3. **Project CRUD** — Create, list, permissions
4. **Custom agent CRUD** — Create, configure, visibility rules
5. **Agent execution** — Mock LLM, verify 3-phase workflow
6. **Scheduling** — cron parsing, RedBeat registration
7. **Knowledge base** — File upload, RAG search accuracy
8. **Frontend: KanbanBoard** — DnD interactions, column rendering
9. **Frontend: AgentHubPage** — Agent list, modal open/close
10. **Frontend: AgentChatPage** — SSE event handling, message display

## pytest.ini / pyproject.toml

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

## Common Test Issues

- **`Event loop closed` errors** — Use `asyncio_mode = "auto"` in pytest config
- **Database already exists** — Use transaction rollback fixtures instead of drop/create
- **Celery tasks run in tests** — Use `CELERY_TASK_ALWAYS_EAGER=True` or mock the task
- **JWT validation in tests** — Use `auth_headers` fixture, don't hardcode tokens
