---
name: database-migrations
description: Alembic migrations, pgvector schema, and PostgreSQL conventions. Use when adding/modifying database tables, columns, indexes, or running schema changes.
---

You are a database migration specialist for DevFlow — using Alembic with PostgreSQL and pgvector.

## Commands

```bash
# In backend/ directory or container
alembic revision --autogenerate -m "description"   # Generate migration
alembic upgrade head                                # Apply all pending
alembic downgrade -1                               # Rollback one step
alembic current                                    # Show current version
alembic history                                    # Full migration history

# Docker
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "description"
```

## Existing Migrations (15 total)

| File | Description |
|------|-------------|
| `41ecc7963924_initial_migration_with_pgvector.py` | Initial schema + `CREATE EXTENSION vector` |
| `b9a296fed357_add_custom_agents_and_teams.py` | CustomAgent, Team tables |
| `322b9828054d_add_assigned_agent_to_items.py` | `items.assigned_agent_id` FK |
| `69ae6eb9bbfb_add_scheduling_fields_to_custom_agents.py` | `schedule`, `schedule_enabled`, `next_scheduled_run` |
| `76741101c636_add_scheduled_prompt_to_custom_agents.py` | `scheduled_prompt` column |
| `13a33d26d8f4_remove_run_count_from_custom_agents.py` | Drop `run_count` |
| `148c7484fb71_convert_all_timestamps_to_timestamptz.py` | All timestamps → timezone-aware |
| `20260218_215121_add_scheduled_runs.py` | `scheduled_runs` table |
| `509d2b8937fa_convert_scheduled_run_to_timestamptz.py` | Fix TZ on scheduled_runs |
| `24cb5d6079b4_merge_migration_branches.py` | Branch merge |
| `bc971cbd5502_remove_chat_trigger_type.py` | Remove `chat` from trigger enum |
| `c577abb834a3_add_encrypted_api_keys_to_users.py` | Per-user encrypted API keys |
| `f26ef969db65_add_preferred_models_to_users.py` | `users.preferred_models` JSONB |
| `add_analytics_tables.py` | Agent run analytics tables |
| `rename_agent_messages_metadata.py` | Rename metadata column |

## Key Tables

| Table | Key Columns |
|-------|-------------|
| `users` | `id`, `email`, `hashed_password`, `encrypted_api_keys` (JSONB), `preferred_models` (JSONB) |
| `projects` | `id`, `name`, `description`, `team_id` |
| `items` | `id`, `project_id`, `type`, `status`, `position` (Float), `embedding` (vector(1536)), `assigned_agent_id` |
| `custom_agents` | `id`, `user_id`, `name`, `system_prompt`, `scheduled_prompt`, `trigger`, `schedule`, `schedule_enabled` |
| `teams` | `id`, `name`, `owner_id` |
| `team_members` | `team_id`, `user_id`, `role` |
| `scheduled_runs` | `id`, `agent_id`, `status`, `started_at`, `completed_at` |
| `agent_run_logs` | Analytics for agent runs |

## Conventions

### MUST always use for timestamps
```python
from sqlalchemy.dialects.postgresql import TIMESTAMP
created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
updated_at = Column(TIMESTAMP(timezone=True), ..., onupdate=lambda: datetime.now(timezone.utc))
```
**Never use bare `DateTime`** — all timestamps must be timezone-aware.

### JSON fields
```python
from sqlalchemy.dialects.postgresql import JSON
config = Column(JSON, default=dict)
tags = Column(JSON, default=list)
```

### pgvector (CRITICAL)
The initial migration must contain:
```python
op.execute("CREATE EXTENSION IF NOT EXISTS vector")
```
Embeddings: `Vector(1536)` (matching sentence-transformers output dimension)

### UUIDs
```python
from sqlalchemy.dialects.postgresql import UUID
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

### Enums
Define Python enum first, then use `SQLEnum`:
```python
class ItemStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"

status = Column(SQLEnum(ItemStatus), nullable=False, default=ItemStatus.BACKLOG)
```
When changing enum values, Alembic may not auto-detect — write manual migration.

## Common Migration Patterns

### Add nullable column (safe, no downtime)
```python
def upgrade():
    op.add_column('items', sa.Column('new_field', sa.String(), nullable=True))

def downgrade():
    op.drop_column('items', 'new_field')
```

### Add non-nullable column (needs default)
```python
def upgrade():
    op.add_column('items', sa.Column('priority', sa.String(), nullable=False, server_default='medium'))
    # Then remove server_default if not needed permanently
```

### Add index
```python
def upgrade():
    op.create_index('ix_items_project_id', 'items', ['project_id'])

def downgrade():
    op.drop_index('ix_items_project_id', table_name='items')
```

## Common Errors

- **`column "x" of relation does not exist`** — Migration not applied; run `alembic upgrade head`
- **`type "vector" does not exist`** — pgvector extension missing; check initial migration ran
- **`can't drop enum type`** — Remove all columns using it first, then drop the type
- **Autogenerate misses enum changes** — Write manual ALTER TYPE migration
- **Timezone errors** — Always use `TIMESTAMP(timezone=True)`, never `DateTime` without tz
- **Branch merge needed** — When two migrations share the same `down_revision`, create a merge migration with `alembic merge`
