"""Add scheduled_prompt to custom_agents

Revision ID: 76741101c636
Revises: 148c7484fb71
Create Date: 2026-02-19 10:40:59.292357

"""
from alembic import op
import sqlalchemy as sa

revision = '76741101c636'
down_revision = '148c7484fb71'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add scheduled_prompt column to custom_agents
    op.add_column('custom_agents', sa.Column('scheduled_prompt', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove scheduled_prompt column
    op.drop_column('custom_agents', 'scheduled_prompt')
