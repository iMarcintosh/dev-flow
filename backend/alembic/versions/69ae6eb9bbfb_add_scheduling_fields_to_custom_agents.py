"""Add scheduling fields to custom agents

Revision ID: 69ae6eb9bbfb
Revises: 24cb5d6079b4
Create Date: 2026-02-18 18:16:25.698178

"""
from alembic import op
import sqlalchemy as sa

revision = "69ae6eb9bbfb"
down_revision = "24cb5d6079b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add scheduling fields to custom_agents table
    op.add_column("custom_agents", sa.Column("trigger", sa.String(length=20), server_default="manual", nullable=False))
    op.add_column("custom_agents", sa.Column("schedule", sa.String(length=100), nullable=True))
    op.add_column("custom_agents", sa.Column("schedule_enabled", sa.Boolean(), server_default="true", nullable=False))
    op.add_column("custom_agents", sa.Column("last_scheduled_run", sa.DateTime(), nullable=True))
    op.add_column("custom_agents", sa.Column("next_scheduled_run", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove scheduling fields from custom_agents table
    op.drop_column("custom_agents", "next_scheduled_run")
    op.drop_column("custom_agents", "last_scheduled_run")
    op.drop_column("custom_agents", "schedule_enabled")
    op.drop_column("custom_agents", "schedule")
    op.drop_column("custom_agents", "trigger")
