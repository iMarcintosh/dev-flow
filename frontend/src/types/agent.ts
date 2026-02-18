export interface AgentInfo {
  name: string
  description: string
  trigger: string
  schedule?: string
}

export interface AgentRun {
  id: string
  agent_name: string
  status: 'pending' | 'running' | 'done' | 'failed'
  input?: any
  output?: any
  error_message?: string
  started_at?: string
  finished_at?: string
  created_at: string
}

export interface AgentLogMessage {
  type: 'agent_log' | 'agent_status' | 'agent_finished'
  run_id: string
  level?: string
  message?: string
  timestamp?: string
  status?: string
  success?: boolean
  result?: any
}

export interface StartAgentRequest {
  project_id: string
  data: {
    text: string
  }
}
