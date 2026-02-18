import api from './api'
import type {
  CustomAgent,
  CustomAgentCreate,
  CustomAgentUpdate,
  AgentTemplate,
  AgentConversation,
  AgentMessage,
} from '@/types/custom-agent'

// Agent Management
export const customAgentService = {
  // List agents
  async listAgents(includeTeam = true): Promise<CustomAgent[]> {
    const { data } = await api.get('/api/custom-agents', {
      params: { include_team: includeTeam },
    })
    return data
  },

  // Get agent by ID
  async getAgent(id: string): Promise<CustomAgent> {
    const { data } = await api.get(`/api/custom-agents/${id}`)
    return data
  },

  // Create agent
  async createAgent(agent: CustomAgentCreate): Promise<CustomAgent> {
    const { data } = await api.post('/api/custom-agents', agent)
    return data
  },

  // Update agent
  async updateAgent(id: string, updates: CustomAgentUpdate): Promise<CustomAgent> {
    const { data } = await api.put(`/api/custom-agents/${id}`, updates)
    return data
  },

  // Delete agent
  async deleteAgent(id: string): Promise<void> {
    await api.delete(`/api/custom-agents/${id}`)
  },

  // Clone agent (marketplace install)
  async cloneAgent(id: string): Promise<CustomAgent> {
    const { data } = await api.post(`/api/custom-agents/${id}/clone`)
    return data
  },

  // Star/unstar agent
  async starAgent(id: string): Promise<void> {
    await api.post(`/api/custom-agents/${id}/star`)
  },

  async unstarAgent(id: string): Promise<void> {
    await api.delete(`/api/custom-agents/${id}/star`)
  },

  // Search marketplace
  async searchMarketplace(query?: string, limit = 50): Promise<CustomAgent[]> {
    const { data } = await api.get('/api/custom-agents/marketplace', {
      params: { query, limit },
    })
    return data
  },

  // Test agent
  async testAgent(
    id: string,
    testInput = 'Hello!'
  ): Promise<{ success: boolean; response?: string; error?: string }> {
    const { data } = await api.post(`/api/custom-agents/${id}/test`, null, {
      params: { test_input: testInput },
    })
    return data
  },
}

// Templates
export const templateService = {
  // List templates
  async listTemplates(): Promise<AgentTemplate[]> {
    const { data } = await api.get('/api/custom-agents/templates')
    return data
  },

  // Create from template
  async createFromTemplate(category: string): Promise<CustomAgent> {
    const { data } = await api.post(`/api/custom-agents/from-template/${category}`)
    return data
  },
}

// Conversations
export const conversationService = {
  // List conversations
  async listConversations(agentId?: string): Promise<AgentConversation[]> {
    const { data } = await api.get('/api/agent-chat/conversations', {
      params: agentId ? { agent_id: agentId } : undefined,
    })
    return data
  },

  // Get conversation
  async getConversation(id: string): Promise<AgentConversation> {
    const { data } = await api.get(`/api/agent-chat/conversations/${id}`)
    return data
  },

  // Create conversation
  async createConversation(agentId: string, projectId?: string): Promise<AgentConversation> {
    const { data } = await api.post('/api/agent-chat/conversations', null, {
      params: { agent_id: agentId, project_id: projectId },
    })
    return data
  },

  // Update conversation title
  async updateTitle(id: string, title: string): Promise<AgentConversation> {
    const { data } = await api.put(`/api/agent-chat/conversations/${id}/title`, null, {
      params: { title },
    })
    return data
  },

  // Delete conversation
  async deleteConversation(id: string): Promise<void> {
    await api.delete(`/api/agent-chat/conversations/${id}`)
  },

  // Get messages
  async getMessages(conversationId: string): Promise<AgentMessage[]> {
    const { data } = await api.get(`/api/agent-chat/conversations/${conversationId}/messages`)
    return data
  },

  // Send message
  async sendMessage(
    conversationId: string,
    message: string
  ): Promise<{
    success: boolean
    user_message?: AgentMessage
    agent_message?: AgentMessage
    error?: string
  }> {
    const { data } = await api.post(
      `/api/agent-chat/conversations/${conversationId}/messages`,
      null,
      {
        params: { message },
      }
    )
    return data
  },
}
