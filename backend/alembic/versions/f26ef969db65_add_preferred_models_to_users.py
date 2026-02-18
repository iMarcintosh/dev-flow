"""add_preferred_models_to_users

Revision ID: f26ef969db65
Revises: 41ecc7963924
Create Date: 2026-02-18 10:48:01.836925

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = 'f26ef969db65'
down_revision = '41ecc7963924'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add preferred_models JSON column to users table
    op.add_column(
        'users',
        sa.Column('preferred_models', JSON, nullable=True)
    )
    
    # Backfill existing users with default models
    op.execute("""
        UPDATE users
        SET preferred_models = '{"task_creator": "claude-3-haiku-20240307", "chat_agent": "claude-3-haiku-20240307"}'::json
        WHERE preferred_models IS NULL
    """)


def downgrade() -> None:
    op.drop_column('users', 'preferred_models')
