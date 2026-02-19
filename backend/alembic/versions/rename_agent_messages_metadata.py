"""rename agent_messages.metadata to message_metadata

Revision ID: rename_agent_msg_metadata
Revises: 509d2b8937fa
Create Date: 2026-02-19

"""
from alembic import op

revision = 'rename_agent_msg_metadata'
down_revision = '76741101c636'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE agent_messages RENAME COLUMN metadata TO message_metadata")


def downgrade() -> None:
    op.execute("ALTER TABLE agent_messages RENAME COLUMN message_metadata TO metadata")
