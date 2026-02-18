import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Play, Clock, CheckCircle, XCircle, Loader2, TrendingUp } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import api from '@/services/api'

interface Agent {
  name: string
  description: string
  trigger: string
  schedule: string | null
}

interface AgentStatus {
  agent: Agent
  status: string
  last_run: {
    id: string
    started_at: string | null
    finished_at: string | null
    status: string
  } | null
  stats: {
    total_runs: number
    successful_runs: number
    success_rate: number
  }
}

interface AgentRun {
  id: string
  agent_name: string
  status: string
  started_at: string | null
  finished_at: string | null
  created_at: string
  error_message: string | null
}

export default function AgentHubPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  
  // Fetch all agents
  const { data: agents = [], isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await api.get<Agent[]>('/api/agents/')
      return data
    },
  })
  
  if (agentsLoading) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </AppLayout>
    )
  }
  
  return (
    <AppLayout>
      <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <h1 className="text-3xl font-bold text-foreground">Agent Hub</h1>
          <p className="text-muted-foreground mt-2">
            Manage and monitor your AI agents
          </p>
        </div>
      </div>
      
      {/* Agent Grid */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <AgentCard
              key={agent.name}
              agent={agent}
              onClick={() => setSelectedAgent(agent.name)}
            />
          ))}
        </div>
        
        {agents.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No agents available</p>
          </div>
        )}
      </div>
      
      {/* Agent Detail Modal */}
      {selectedAgent && (
        <AgentDetailModal
          agentName={selectedAgent}
          onClose={() => setSelectedAgent(null)}
        />
      )}
      </div>
    </AppLayout>
  )
}

function AgentCard({ agent, onClick }: { agent: Agent; onClick: () => void }) {
  const { data: status } = useQuery({
    queryKey: ['agent-status', agent.name],
    queryFn: async () => {
      const { data } = await api.get<AgentStatus>(`/api/agents/${agent.name}/status`)
      return data
    },
    refetchInterval: 5000, // Refresh every 5s
  })
  
  const queryClient = useQueryClient()
  
  const runAgent = useMutation({
    mutationFn: async () => {
      // For now, use a default project (first one)
      const { data: projects } = await api.get('/api/projects/')
      const projectId = projects[0]?.id
      
      if (!projectId) {
        throw new Error('No project available')
      }
      
      await api.post(`/api/agents/${agent.name}/run`, {
        project_id: projectId,
        data: {}
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-status', agent.name] })
    },
  })
  
  const isRunning = status?.status === 'running' || status?.status === 'pending'
  const isManual = agent.trigger === 'manual'
  const isScheduled = agent.trigger === 'scheduled'
  
  return (
    <div
      onClick={onClick}
      className="bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-colors cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">{agent.name}</h3>
          <p className="text-sm text-muted-foreground mt-1">{agent.description}</p>
        </div>
        
        {isRunning && (
          <Loader2 className="w-5 h-5 text-blue-500 animate-spin flex-shrink-0 ml-2" />
        )}
      </div>
      
      {/* Trigger Type */}
      <div className="flex items-center gap-2 mb-4">
        {isScheduled && <Clock className="w-4 h-4 text-indigo-500" />}
        {isManual && <Play className="w-4 h-4 text-green-500" />}
        
        <span className="text-xs text-muted-foreground">
          {agent.trigger}
          {agent.schedule && ` • ${agent.schedule}`}
        </span>
      </div>
      
      {/* Stats */}
      {status && (
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-2xl font-bold text-foreground">
              {status.stats.total_runs}
            </div>
            <div className="text-xs text-muted-foreground">Total Runs</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-500">
              {Math.round(status.stats.success_rate)}%
            </div>
            <div className="text-xs text-muted-foreground">Success Rate</div>
          </div>
        </div>
      )}
      
      {/* Last Run */}
      {status?.last_run && (
        <div className="text-xs text-muted-foreground mb-4">
          Last run:{' '}
          {status.last_run.finished_at
            ? new Date(status.last_run.finished_at).toLocaleString()
            : 'In progress'}
        </div>
      )}
      
      {/* Run Button */}
      {isManual && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            runAgent.mutate()
          }}
          disabled={isRunning || runAgent.isPending}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning || runAgent.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Now
            </>
          )}
        </button>
      )}
    </div>
  )
}

function AgentDetailModal({ agentName, onClose }: { agentName: string; onClose: () => void }) {
  const { data: runs = [] } = useQuery({
    queryKey: ['agent-runs', agentName],
    queryFn: async () => {
      const { data } = await api.get<AgentRun[]>(`/api/agents/${agentName}/runs?limit=20`)
      return data
    },
  })
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-xl font-bold text-foreground">{agentName}</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            ✕
          </button>
        </div>
        
        {/* Run History */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Run History</h3>
          
          <div className="space-y-3">
            {runs.map((run) => (
              <div
                key={run.id}
                className="bg-background border border-border rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {run.status === 'done' && <CheckCircle className="w-5 h-5 text-green-500" />}
                    {run.status === 'failed' && <XCircle className="w-5 h-5 text-red-500" />}
                    {(run.status === 'running' || run.status === 'pending') && (
                      <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    )}
                    
                    <span className="font-medium text-foreground">
                      {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
                    </span>
                  </div>
                  
                  <span className="text-sm text-muted-foreground">
                    {new Date(run.created_at).toLocaleString()}
                  </span>
                </div>
                
                {run.error_message && (
                  <div className="text-sm text-red-500 bg-red-500/10 rounded p-2 mt-2">
                    {run.error_message}
                  </div>
                )}
                
                {run.started_at && run.finished_at && (
                  <div className="text-xs text-muted-foreground mt-2">
                    Duration:{' '}
                    {Math.round(
                      (new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) /
                        1000
                    )}
                    s
                  </div>
                )}
              </div>
            ))}
            
            {runs.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No runs yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
