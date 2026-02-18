"""add_assigned_agent_to_items

Revision ID: 322b9828054d
Revises: b9a296fed357
Create Date: 2026-02-18 12:51:14.110694

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '322b9828054d'
down_revision = 'b9a296fed357'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add assigned_agent_id column to items table
    op.add_column('items', sa.Column('assigned_agent_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_items_assigned_agent',
        'items',
        'custom_agents',
        ['assigned_agent_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_items_assigned_agent', 'items', type_='foreignkey')
    op.drop_column('items', 'assigned_agent_id')
