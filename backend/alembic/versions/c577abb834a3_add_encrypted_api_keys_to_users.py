"""add_encrypted_api_keys_to_users

Revision ID: c577abb834a3
Revises: f26ef969db65
Create Date: 2026-02-18 11:41:50.476226

"""
from alembic import op
import sqlalchemy as sa


revision = 'c577abb834a3'
down_revision = 'f26ef969db65'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add encrypted API key columns to users table."""
    # Add columns for encrypted API keys
    op.add_column('users', sa.Column('encrypted_anthropic_key', sa.String(length=512), nullable=True))
    op.add_column('users', sa.Column('encrypted_openai_key', sa.String(length=512), nullable=True))
    op.add_column('users', sa.Column('encrypted_openrouter_key', sa.String(length=512), nullable=True))


def downgrade() -> None:
    """Remove encrypted API key columns from users table."""
    op.drop_column('users', 'encrypted_openrouter_key')
    op.drop_column('users', 'encrypted_openai_key')
    op.drop_column('users', 'encrypted_anthropic_key')
