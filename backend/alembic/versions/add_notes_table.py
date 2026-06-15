"""add notes table

Revision ID: add_notes_table
Revises: rename_agent_msg_metadata
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_notes_table'
down_revision = 'rename_agent_msg_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(500), nullable=False, server_default='Untitled'),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('chroma_indexed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notes_user_id', 'notes', ['user_id'])
    op.create_index('ix_notes_project_id', 'notes', ['project_id'])
    op.create_index('ix_notes_user_id_is_pinned', 'notes', ['user_id', 'is_pinned'])
    op.create_index('ix_notes_user_id_updated_at', 'notes', ['user_id', 'updated_at'])


def downgrade() -> None:
    op.drop_index('ix_notes_user_id_updated_at', table_name='notes')
    op.drop_index('ix_notes_user_id_is_pinned', table_name='notes')
    op.drop_index('ix_notes_project_id', table_name='notes')
    op.drop_index('ix_notes_user_id', table_name='notes')
    op.drop_table('notes')
