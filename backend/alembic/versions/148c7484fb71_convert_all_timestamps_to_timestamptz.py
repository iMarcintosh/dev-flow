"""convert_all_timestamps_to_timestamptz

Revision ID: 148c7484fb71
Revises: 509d2b8937fa
Create Date: 2026-02-19 09:11:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '148c7484fb71'
down_revision = '509d2b8937fa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert all user-facing timestamp columns to timestamptz
    op.execute("ALTER TABLE agent_runs ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_runs ALTER COLUMN started_at TYPE timestamptz USING started_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_runs ALTER COLUMN finished_at TYPE timestamptz USING finished_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE chat_messages ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE items ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE items ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE custom_agents ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE custom_agents ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE custom_agents ALTER COLUMN last_used_at TYPE timestamptz USING last_used_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE agent_analytics ALTER COLUMN date TYPE timestamptz USING date AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_analytics ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_analytics ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE scheduled_agent_runs ALTER COLUMN executed_at TYPE timestamptz USING executed_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    # Revert to timestamp without timezone
    op.execute("ALTER TABLE agent_runs ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_runs ALTER COLUMN started_at TYPE timestamp USING started_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_runs ALTER COLUMN finished_at TYPE timestamp USING finished_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE chat_messages ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE items ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE items ALTER COLUMN updated_at TYPE timestamp USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE custom_agents ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE custom_agents ALTER COLUMN updated_at TYPE timestamp USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE custom_agents ALTER COLUMN last_used_at TYPE timestamp USING last_used_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE agent_analytics ALTER COLUMN date TYPE timestamp USING date AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_analytics ALTER COLUMN created_at TYPE timestamp USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_analytics ALTER COLUMN updated_at TYPE timestamp USING updated_at AT TIME ZONE 'UTC'")
    
    op.execute("ALTER TABLE scheduled_agent_runs ALTER COLUMN executed_at TYPE timestamp USING executed_at AT TIME ZONE 'UTC'")
