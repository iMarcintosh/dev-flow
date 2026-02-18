import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, X, Loader2 } from 'lucide-react'
import { customAgentService } from '@/services/custom-agents'
import api from '@/services/api'
import type { Item } from '@/types'

interface AgentAssignButtonProps {
  item: Item
  projectId: string
}

export function AgentAssignButton({ item, projectId }: AgentAssignButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  // Fetch user's agents
  const { data: agents = [] } = useQuery({
    queryKey: ['custom-agents'],
    queryFn: () => customAgentService.listAgents(true),
  })

  // Assign agent mutation
  const assignMutation = useMutation({
    mutationFn: (agentId: string) =>
      api.post(`/api/items/${item.id}/assign-agent`, { agent_id: agentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-items', projectId] })
      setIsOpen(false)
    },
  })

  // Unassign agent mutation
  const unassignMutation = useMutation({
    mutationFn: () => api.delete(`/api/items/${item.id}/assign-agent`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-items', projectId] })
    },
  })

  const handleAssign = (agentId: string) => {
    assignMutation.mutate(agentId)
  }

  const handleUnassign = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Remove agent assignment?')) {
      unassignMutation.mutate()
    }
  }

  if (item.assigned_agent_id && !isOpen) {
    return (
      <button
        onClick={handleUnassign}
        disabled={unassignMutation.isPending}
        className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors disabled:opacity-50"
        title="Remove agent"
      >
        {unassignMutation.isPending ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : (
          <X className="w-3 h-3" />
        )}
      </button>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(!isOpen)
        }}
        className="flex items-center gap-1.5 px-2 py-1 text-xs bg-accent hover:bg-accent/80 border border-border rounded transition-colors"
      >
        <Bot className="w-3 h-3" />
        Assign Agent
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 mt-1 w-64 bg-card border border-border rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
            <div className="p-2 border-b border-border">
              <p className="text-xs text-muted-foreground">Select an agent</p>
            </div>
            <div className="p-1">
              {agents.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No agents available
                </div>
              ) : (
                agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleAssign(agent.id)
                    }}
                    disabled={assignMutation.isPending}
                    className="w-full flex items-center gap-2 px-3 py-2 hover:bg-accent rounded transition-colors disabled:opacity-50 text-left"
                  >
                    <span className="text-lg">{agent.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-foreground truncate">
                        {agent.name}
                      </div>
                      <div className="text-xs text-muted-foreground truncate">
                        {agent.description}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
