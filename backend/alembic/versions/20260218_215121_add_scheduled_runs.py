"""Migration: Add scheduled_agent_runs table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_scheduled_runs'
down_revision = '13a33d26d8f4'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'scheduled_agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),  # 'success', 'failed'
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('tools_used', sa.Integer(), default=0),
        sa.Column('executed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['custom_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    op.create_index('idx_scheduled_runs_agent', 'scheduled_agent_runs', ['agent_id', 'executed_at'])
    op.create_index('idx_scheduled_runs_user', 'scheduled_agent_runs', ['user_id', 'executed_at'])

def downgrade():
    op.drop_index('idx_scheduled_runs_user', table_name='scheduled_agent_runs')
    op.drop_index('idx_scheduled_runs_agent', table_name='scheduled_agent_runs')
    op.drop_table('scheduled_agent_runs')
