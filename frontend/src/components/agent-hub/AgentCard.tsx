import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { 
  Edit2, Trash2, MessageSquare, Star, Download, Lock, Users, Globe, Clock,
  Activity, Cpu, Search, Code, FileText, Trello 
} from 'lucide-react'
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
  const [isHovered, setIsHovered] = useState(false)

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
    private: <Lock className="w-3.5 h-3.5" />,
    team: <Users className="w-3.5 h-3.5" />,
    public: <Globe className="w-3.5 h-3.5" />,
  }[agent.visibility]

  const visibilityColor = {
    private: 'text-yellow-500 bg-yellow-500/10',
    team: 'text-blue-500 bg-blue-500/10',
    public: 'text-green-500 bg-green-500/10',
  }[agent.visibility]

  const toolIcons: Record<string, any> = {
    web_search: Search,
    code_execution: Code,
    knowledge_base: FileText,
    board: Trello,
  }

  return (
    <>
      <div 
        onClick={onViewDetails}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="relative bg-card border border-border rounded-xl transition-all duration-300 ease-out hover:shadow-2xl hover:border-primary/50 cursor-pointer group overflow-hidden flex flex-col h-[420px]"
      >
        {/* Diagonal Shine Effect Overlay */}
        <div 
          className="absolute inset-0 pointer-events-none overflow-hidden"
          style={{
            opacity: isHovered ? 1 : 0,
            transition: isHovered 
              ? 'opacity 0.3s ease-out 0.4s' 
              : 'opacity 0.2s ease-out'
          }}
        >
          <div 
            className="absolute top-0 left-0 w-[250%] h-[250%]"
            style={{
              background: 'linear-gradient(120deg, transparent 0%, transparent 45%, rgba(255,255,255,0.25) 50%, transparent 55%, transparent 100%)',
              filter: 'blur(12px)',
              transform: isHovered 
                ? 'translate(20%, 20%)' 
                : 'translate(-120%, -120%)',
              transition: isHovered 
                ? 'transform 1.2s ease-out' 
                : 'none'
            }}
          />
        </div>

        {/* Visibility Badge - Top Right */}
        <div className={`absolute top-4 right-4 z-10 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${visibilityColor} border border-current/20`}>
          {visibilityIcon}
          <span className="capitalize">{agent.visibility}</span>
        </div>

        {/* Action Buttons - Top Right on Hover, below badge */}
        {!isMarketplace && (
          <div className="absolute top-16 right-4 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-all duration-300 z-20">
            <button
              onClick={handleEdit}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-background/95 backdrop-blur-sm border-2 border-border hover:bg-accent hover:border-primary transition-colors shadow-lg"
              title="Edit Agent"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-background/95 backdrop-blur-sm border-2 border-border hover:bg-red-500 hover:text-white hover:border-red-600 transition-colors disabled:opacity-50 shadow-lg"
              title="Delete Agent"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Content Wrapper - flex-1 to push button down */}
        <div className="p-6 space-y-4 flex-1 overflow-hidden relative z-10">
          {/* Header */}
          <div className="flex items-start gap-4 pr-24">
            <div className="text-5xl flex-shrink-0">{agent.icon}</div>
            <div className="flex-1 min-w-0">
              <h3 className="text-xl font-bold text-foreground mb-1 truncate">{agent.name}</h3>
              <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">{agent.description}</p>
            </div>
          </div>

          {/* Schedule Badge (if applicable) */}
          {agent.trigger === 'scheduled' && agent.schedule && (
            <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 border border-primary/20 rounded-lg">
              <Clock className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">Scheduled</span>
              {agent.next_scheduled_run && (
                <span className="text-xs text-muted-foreground ml-auto">
                  Next: {new Date(agent.next_scheduled_run).toLocaleTimeString()}
                </span>
              )}
            </div>
          )}

          {/* Divider */}
          <div className="border-t border-border/50" />

          {/* Footer - Stats & Tools */}
          <div className="space-y-3">
            {/* Stats Row */}
            <div className="flex items-center gap-4 text-sm">
              {/* Runs */}
              <div className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors">
                <Activity className="w-4 h-4" />
                <span className="font-semibold">{agent.run_count || 0}</span>
              </div>

              {/* Stars */}
              <div className="flex items-center gap-1.5 text-yellow-500">
                <Star className="w-4 h-4 fill-yellow-500" />
                <span className="font-semibold">{agent.star_count || 0}</span>
              </div>

              {/* Installs (Marketplace only) */}
              {isMarketplace && (
                <div className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors">
                  <Download className="w-4 h-4" />
                  <span className="font-semibold">{agent.install_count || 0}</span>
                </div>
              )}

              {/* Separator */}
              <div className="h-4 w-px bg-border" />

              {/* Tools Icons */}
              {agent.enabled_tools && agent.enabled_tools.length > 0 && (
                <div className="flex items-center gap-1.5 flex-1">
                  {agent.enabled_tools.slice(0, 4).map((tool) => {
                    const Icon = toolIcons[tool] || Code
                    return (
                      <div
                        key={tool}
                        className="w-7 h-7 flex items-center justify-center rounded-lg bg-primary/10 text-primary"
                        title={tool}
                      >
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                    )
                  })}
                  {agent.enabled_tools.length > 4 && (
                    <div className="w-7 h-7 flex items-center justify-center rounded-lg bg-muted text-xs font-medium text-muted-foreground">
                      +{agent.enabled_tools.length - 4}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Model Badge */}
            <div className="flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-mono text-muted-foreground truncate" title={agent.model_name}>
                {agent.model_name}
              </span>
            </div>
          </div>
        </div>

        {/* Actions - Always at Bottom */}
        <div className="px-6 pb-6 pt-0 mt-auto relative z-10">
          {isMarketplace ? (
            <button
              onClick={handleInstall}
              disabled={cloneMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 font-medium"
            >
              <Download className="w-4 h-4" />
              {cloneMutation.isPending ? 'Installing...' : 'Install'}
            </button>
          ) : (
            <button
              onClick={handleChat}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
            >
              <MessageSquare className="w-4 h-4" />
              Chat
            </button>
          )}
        </div>
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
    </>
  )
}
