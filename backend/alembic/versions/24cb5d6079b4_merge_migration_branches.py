"""Merge migration branches

Revision ID: 24cb5d6079b4
Revises: 322b9828054d, add_analytics_001
Create Date: 2026-02-18 18:16:11.643815

"""
from alembic import op
import sqlalchemy as sa


revision = '24cb5d6079b4'
down_revision = ('322b9828054d', 'add_analytics_001')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
