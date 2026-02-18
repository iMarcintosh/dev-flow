"""Remove run_count from custom_agents

Revision ID: 13a33d26d8f4
Revises: bc971cbd5502
Create Date: 2026-02-18 19:29:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "13a33d26d8f4"
down_revision = "bc971cbd5502"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove redundant run_count column
    # Analytics table (agent_analytics.total_runs) is now the single source of truth
    op.drop_column("custom_agents", "run_count")


def downgrade() -> None:
    # Re-add run_count column if needed
    op.add_column("custom_agents", sa.Column("run_count", sa.Integer(), server_default="0", nullable=False))
