"""add_custom_agents_and_teams

Revision ID: b9a296fed357
Revises: c577abb834a3
Create Date: 2026-02-18 12:12:31.587404

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'b9a296fed357'
down_revision = 'c577abb834a3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_teams_created_by', 'teams', ['created_by'])
    
    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),  # 'owner', 'admin', 'member'
        sa.Column('joined_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    op.create_unique_constraint('uq_team_members_team_user', 'team_members', ['team_id', 'user_id'])
    
    # Create custom_agents table
    op.create_table(
        'custom_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='SET NULL'), nullable=True),
        
        # Basic info
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),  # Emoji or icon name
        sa.Column('visibility', sa.String(20), nullable=False, server_default='private'),  # 'private', 'team', 'public'
        
        # Template metadata
        sa.Column('is_template', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('custom_agents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),  # 'code_review', 'testing', 'documentation', etc.
        
        # LLM configuration
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('system_prompt', sa.Text, nullable=False),
        sa.Column('temperature', sa.Float, nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer, nullable=False, server_default='4096'),
        sa.Column('top_p', sa.Float, nullable=False, server_default='1.0'),
        
        # Tools & capabilities
        sa.Column('enabled_tools', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('tool_config', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Stats
        sa.Column('run_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('star_count', sa.Integer, nullable=False, server_default='0'),  # For marketplace
        sa.Column('install_count', sa.Integer, nullable=False, server_default='0'),  # For marketplace
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_custom_agents_user_id', 'custom_agents', ['user_id'])
    op.create_index('ix_custom_agents_team_id', 'custom_agents', ['team_id'])
    op.create_index('ix_custom_agents_visibility', 'custom_agents', ['visibility'])
    op.create_index('ix_custom_agents_category', 'custom_agents', ['category'])
    
    # Create agent_knowledge_files table (for RAG)
    op.create_table(
        'agent_knowledge_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),  # 'pdf', 'markdown', 'code', 'text'
        sa.Column('file_size', sa.Integer, nullable=False),  # bytes
        sa.Column('content_hash', sa.String(64), nullable=False),  # SHA256 hash
        sa.Column('storage_path', sa.String(512), nullable=False),  # Path in storage
        
        # Processing status
        sa.Column('processed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('chunk_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('embedding_model', sa.String(100), nullable=True),
        
        sa.Column('uploaded_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_agent_knowledge_files_agent_id', 'agent_knowledge_files', ['agent_id'])
    
    # Create agent_conversations table
    op.create_table(
        'agent_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        
        sa.Column('title', sa.String(255), nullable=True),  # Auto-generated from first message
        sa.Column('message_count', sa.Integer, nullable=False, server_default='0'),
        
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_agent_conversations_agent_id', 'agent_conversations', ['agent_id'])
    op.create_index('ix_agent_conversations_user_id', 'agent_conversations', ['user_id'])
    
    # Create agent_messages table
    op.create_table(
        'agent_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_conversations.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('role', sa.String(20), nullable=False),  # 'user', 'assistant', 'system', 'tool'
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),  # Tool calls, citations, etc.
        
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_agent_messages_conversation_id', 'agent_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_table('agent_messages')
    op.drop_table('agent_conversations')
    op.drop_table('agent_knowledge_files')
    op.drop_table('custom_agents')
    op.drop_table('team_members')
    op.drop_table('teams')
