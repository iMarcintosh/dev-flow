/**
 * Analytics Service
 * 
 * Fetches analytics data for custom agents (Phase 8D system)
 */
import api from './api'

export interface AgentSummary {
  total_runs: number
  successful_runs: number
  failed_runs: number
  success_rate: number
  avg_response_time: number
  min_response_time?: number
  max_response_time?: number
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  tool_calls_count: number
}

export interface TimelineData {
  date: string
  total_runs: number
  successful_runs: number
  failed_runs: number
  avg_response_time: number
  total_tokens: number
}

export interface ToolUsageStat {
  tool_name: string
  usage_count: number
  success_count: number
  failed_count: number
  success_rate: number
  avg_execution_time?: number
}

/**
 * Get analytics summary for an agent
 */
export async function getAgentSummary(agentId: string, days: number = 30): Promise<AgentSummary | null> {
  try {
    const { data } = await api.get(`/api/analytics/agents/${agentId}/summary`, {
      params: { days }
    })
    return data
  } catch (error: any) {
    // Return null if no analytics data yet (404)
    if (error.response?.status === 404) {
      return null
    }
    throw error
  }
}

/**
 * Get timeline analytics for an agent
 */
export async function getAgentTimeline(agentId: string, days: number = 30): Promise<TimelineData[]> {
  try {
    const { data } = await api.get(`/api/analytics/agents/${agentId}`, {
      params: { days }
    })
    return data
  } catch (error: any) {
    if (error.response?.status === 404) {
      return []
    }
    throw error
  }
}

/**
 * Get tool usage statistics for an agent
 */
export async function getAgentToolUsage(agentId: string, days: number = 30): Promise<ToolUsageStat[]> {
  try {
    const { data } = await api.get(`/api/analytics/agents/${agentId}/tools`, {
      params: { days }
    })
    return data
  } catch (error: any) {
    if (error.response?.status === 404) {
      return []
    }
    throw error
  }
}

/**
 * Get total lifetime runs for an agent (for display on cards)
 */
export async function getAgentTotalRuns(agentId: string): Promise<number> {
  try {
    const { data } = await api.get(`/api/analytics/agents/${agentId}/total-runs`)
    return data.total_runs || 0
  } catch (error: any) {
    // Return 0 if no analytics data yet
    if (error.response?.status === 404) {
      return 0
    }
    console.error('Failed to fetch agent total runs:', error)
    return 0
  }
}
