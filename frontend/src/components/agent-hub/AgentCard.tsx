import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Edit2, Trash2, MessageSquare, Star, Download, Lock, Users, Globe } from 'lucide-react'
import { customAgentService } from '@/services/custom-agents'
import type { CustomAgent } from '@/types/custom-agent'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'

interface AgentCardProps {
  agent: CustomAgent
  isMarketplace?: boolean
  onEdit?: () => void
  onDeleted?: () => void
  onInstalled?: () => void
  onViewDetails?: () => void
}

export function AgentCard({
  agent,
  isMarketplace = false,
  onEdit,
  onDeleted,
  onInstalled,
  onViewDetails,
}: AgentCardProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const deleteMutation = useMutation({
    mutationFn: () => customAgentService.deleteAgent(agent.id),
    onSuccess: () => {
      onDeleted?.()
      setShowDeleteConfirm(false)
    },
  })

  const cloneMutation = useMutation({
    mutationFn: () => customAgentService.cloneAgent(agent.id),
    onSuccess: () => {
      onInstalled?.()
    },
  })

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowDeleteConfirm(true)
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit?.()
  }

  const handleChat = (e: React.MouseEvent) => {
    e.stopPropagation()
    window.location.href = `/chat?agent_id=${agent.id}`
  }

  const handleInstall = (e: React.MouseEvent) => {
    e.stopPropagation()
    cloneMutation.mutate()
  }

  const visibilityIcon = {
    private: <Lock className="w-4 h-4" />,
    team: <Users className="w-4 h-4" />,
    public: <Globe className="w-4 h-4" />,
  }[agent.visibility]

  const visibilityColor = {
    private: 'text-yellow-500',
    team: 'text-blue-500',
    public: 'text-green-500',
  }[agent.visibility]

  return (
    <div className="bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-all hover:shadow-lg group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="text-4xl">{agent.icon}</div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-foreground truncate">{agent.name}</h3>
            <p className="text-sm text-muted-foreground line-clamp-2">{agent.description}</p>
          </div>
        </div>
      </div>

      {/* Model & Visibility */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-background px-2 py-1 rounded">
          <span className="font-mono">{agent.model_name.split('-').slice(0, 2).join('-')}</span>
        </div>
        <div className={`flex items-center gap-1.5 text-xs ${visibilityColor}`}>
          {visibilityIcon}
          <span className="capitalize">{agent.visibility}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <div className="text-lg font-bold text-foreground">{agent.run_count}</div>
          <div className="text-xs text-muted-foreground">Runs</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-foreground flex items-center justify-center gap-1">
            <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
            {agent.star_count}
          </div>
          <div className="text-xs text-muted-foreground">Stars</div>
        </div>
        {isMarketplace && (
          <div className="text-center">
            <div className="text-lg font-bold text-foreground">{agent.install_count}</div>
            <div className="text-xs text-muted-foreground">Installs</div>
          </div>
        )}
      </div>

      {/* Tools */}
      {agent.enabled_tools && agent.enabled_tools.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-muted-foreground mb-2">Tools:</div>
          <div className="flex flex-wrap gap-1">
            {agent.enabled_tools.slice(0, 3).map((tool) => (
              <span
                key={tool}
                className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded"
              >
                {tool}
              </span>
            ))}
            {agent.enabled_tools.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{agent.enabled_tools.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-4 border-t border-border">
        {isMarketplace ? (
          <button
            onClick={handleInstall}
            disabled={cloneMutation.isPending}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {cloneMutation.isPending ? 'Installing...' : 'Install'}
          </button>
        ) : (
          <>
            <button
              onClick={handleChat}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              <MessageSquare className="w-4 h-4" />
              Chat
            </button>
            <button
              onClick={handleEdit}
              className="px-3 py-2 bg-background border border-border rounded-lg hover:bg-accent transition-colors"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="px-3 py-2 bg-background border border-border rounded-lg hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-500 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={() => deleteMutation.mutate()}
        title="Delete Agent"
        message={`Are you sure you want to delete "${agent.name}"?\n\nThis will also delete all conversations and knowledge base data associated with this agent. This action cannot be undone.`}
        confirmText="Delete Agent"
        confirmVariant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
