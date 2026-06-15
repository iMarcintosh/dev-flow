"""add analytics tables

Revision ID: add_analytics_001
Revises: 
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_analytics_001'
down_revision = 'b9a296fed357'
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_analytics table
    op.create_table(
        'agent_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_runs', sa.Integer(), default=0),
        sa.Column('successful_runs', sa.Integer(), default=0),
        sa.Column('failed_runs', sa.Integer(), default=0),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('min_response_time', sa.Float(), nullable=True),
        sa.Column('max_response_time', sa.Float(), nullable=True),
        sa.Column('total_response_time', sa.Float(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('prompt_tokens', sa.Integer(), default=0),
        sa.Column('completion_tokens', sa.Integer(), default=0),
        sa.Column('tool_calls_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['custom_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create tool_usage_logs table
    op.create_table(
        'tool_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['custom_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes
    op.create_index('idx_agent_analytics_agent_date', 'agent_analytics', ['agent_id', 'date'])
    op.create_index('idx_agent_analytics_user_date', 'agent_analytics', ['user_id', 'date'])
    op.create_index('idx_tool_usage_agent', 'tool_usage_logs', ['agent_id'])
    op.create_index('idx_tool_usage_timestamp', 'tool_usage_logs', ['timestamp'])


def downgrade():
    op.drop_index('idx_tool_usage_timestamp')
    op.drop_index('idx_tool_usage_agent')
    op.drop_index('idx_agent_analytics_user_date')
    op.drop_index('idx_agent_analytics_agent_date')
    op.drop_table('tool_usage_logs')
    op.drop_table('agent_analytics')
