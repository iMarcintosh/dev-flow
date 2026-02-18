import { useQuery } from '@tanstack/react-query'
import { Bot } from 'lucide-react'
import { customAgentService } from '@/services/custom-agents'

interface AgentBadgeProps {
  agentId: string
  size?: 'sm' | 'md'
}

export function AgentBadge({ agentId, size = 'sm' }: AgentBadgeProps) {
  const { data: agent } = useQuery({
    queryKey: ['custom-agent', agentId],
    queryFn: () => customAgentService.getAgent(agentId),
    enabled: !!agentId,
  })

  if (!agent) return null

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 bg-primary/10 text-primary border border-primary/30 rounded ${sizeClasses[size]}`}
      title={`Assigned to ${agent.name}`}
    >
      <span className="text-base">{agent.icon}</span>
      <span className="font-medium">{agent.name}</span>
    </div>
  )
}
