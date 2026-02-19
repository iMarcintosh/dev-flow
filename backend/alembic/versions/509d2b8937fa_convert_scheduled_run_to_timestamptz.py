"""convert_scheduled_run_to_timestamptz

Revision ID: 509d2b8937fa
Revises: add_scheduled_runs
Create Date: 2026-02-19 09:08:52.222480

"""
from alembic import op
import sqlalchemy as sa


revision = '509d2b8937fa'
down_revision = 'add_scheduled_runs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert scheduling columns from timestamp to timestamptz (timezone-aware)
    op.execute("ALTER TABLE custom_agents ALTER COLUMN next_scheduled_run TYPE timestamptz USING next_scheduled_run AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE custom_agents ALTER COLUMN last_scheduled_run TYPE timestamptz USING last_scheduled_run AT TIME ZONE 'UTC'")


def downgrade() -> None:
    # Revert to timestamp without timezone
    op.execute("ALTER TABLE custom_agents ALTER COLUMN next_scheduled_run TYPE timestamp USING next_scheduled_run AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE custom_agents ALTER COLUMN last_scheduled_run TYPE timestamp USING last_scheduled_run AT TIME ZONE 'UTC'")
