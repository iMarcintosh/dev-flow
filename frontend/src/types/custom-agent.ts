export interface CustomAgent {
  id: string
  user_id: string
  team_id?: string
  name: string
  description?: string
  icon: string
  visibility: 'private' | 'team' | 'public'
  model_name: string
  system_prompt: string
  temperature: number
  max_tokens?: number
  top_p?: number
  enabled_tools: string[]
  tool_config?: Record<string, any>
  run_count: number
  star_count: number
  install_count: number
  created_at: string
  updated_at: string
  last_used_at?: string
}

export interface CustomAgentCreate {
  name: string
  description?: string
  icon?: string
  visibility?: 'private' | 'team' | 'public'
  model_name: string
  system_prompt: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  enabled_tools?: string[]
  tool_config?: Record<string, any>
  team_id?: string
}

export interface CustomAgentUpdate {
  name?: string
  description?: string
  icon?: string
  visibility?: 'private' | 'team' | 'public'
  model_name?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  enabled_tools?: string[]
  tool_config?: Record<string, any>
  team_id?: string
}

export interface AgentTemplate {
  category: string
  name: string
  description: string
  icon: string
  model_name: string
  system_prompt: string
  temperature: number
  max_tokens?: number
  enabled_tools: string[]
  tool_config?: Record<string, any>
}

export interface AgentConversation {
  id: string
  agent_id: string
  user_id: string
  project_id?: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface AgentMessage {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  message_metadata?: Record<string, any>
  created_at: string
}

export const AVAILABLE_TOOLS = [
  { id: 'board', name: 'Board Tools', description: 'Create and manage board items' },
  { id: 'web_search', name: 'Web Search', description: 'Search the web for information' },
  { id: 'code_execution', name: 'Code Execution', description: 'Execute code in Docker sandbox' },
  { id: 'code_analysis', name: 'Code Analysis', description: 'Analyze code structure and quality' },
  { id: 'knowledge_base', name: 'Knowledge Base', description: 'Search agent knowledge files' },
  { id: 'git', name: 'Git Operations', description: 'Git commands and repository operations' },
]

export const DEFAULT_AGENT_ICON = '🤖'
