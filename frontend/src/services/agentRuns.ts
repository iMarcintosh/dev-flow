/**
 * Agent Runs Service
 * 
 * Fetches agent run data from legacy system (TaskCreator, DailySummary, etc.)
 */
import api from './api'

export enum AgentRunStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  DONE = 'done',
  FAILED = 'failed'
}

export interface AgentRun {
  id: string
  agent_name: string
  status: AgentRunStatus
  input?: any
  output?: any
  error_message?: string
  started_at?: string
  finished_at?: string
  created_at: string
}

export interface AgentRunLog {
  id: string
  agent_run_id: string
  level: string  // 'info' | 'warning' | 'error'
  message: string
  timestamp: string
}

/**
 * Get recent runs for an agent
 */
export async function getAgentRuns(agentName: string, limit: number = 10): Promise<AgentRun[]> {
  try {
    const { data } = await api.get(`/api/agents/${agentName}/runs`, {
      params: { limit }
    })
    return data
  } catch (error: any) {
    // No runs yet or agent doesn't exist in legacy system
    if (error.response?.status === 404) {
      return []
    }
    throw error
  }
}

/**
 * Get details for a specific agent run
 */
export async function getAgentRunDetails(runId: string): Promise<AgentRun | null> {
  try {
    const { data } = await api.get(`/api/agents/runs/${runId}`)
    return data
  } catch (error: any) {
    if (error.response?.status === 404) {
      return null
    }
    throw error
  }
}

/**
 * Get logs for a specific agent run
 */
export async function getAgentRunLogs(runId: string): Promise<AgentRunLog[]> {
  try {
    const { data } = await api.get(`/api/agents/runs/${runId}/logs`)
    return data
  } catch (error: any) {
    if (error.response?.status === 404) {
      return []
    }
    throw error
  }
}
