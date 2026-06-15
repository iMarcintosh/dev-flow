import { Plus, Trash2, MessageSquare } from 'lucide-react'
import type { AgentConversation } from '@/types/custom-agent'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { conversationService } from '@/services/custom-agents'

interface ConversationListProps {
  conversations: AgentConversation[]
  selectedId?: string
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
  isCreating: boolean
}

export function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNew,
  onDelete,
  isCreating,
}: ConversationListProps) {
  return (
    <div className="w-80 border-r border-border bg-card flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <button
          onClick={onNew}
          disabled={isCreating}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          {isCreating ? 'Creating...' : 'New Conversation'}
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-8 text-center">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-sm text-muted-foreground">No conversations yet</p>
            <p className="text-xs text-muted-foreground mt-1">Click above to start chatting</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {conversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isSelected={conversation.id === selectedId}
                onSelect={() => onSelect(conversation.id)}
                onDelete={() => onDelete(conversation.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface ConversationItemProps {
  conversation: AgentConversation
  isSelected: boolean
  onSelect: () => void
  onDelete: () => void
}

function ConversationItem({ conversation, isSelected, onSelect, onDelete }: ConversationItemProps) {
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: () => conversationService.deleteConversation(conversation.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-conversations'] })
      onDelete()
    },
  })

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm(`Delete conversation "${conversation.title}"?`)) {
      deleteMutation.mutate()
    }
  }

  return (
    <div
      onClick={onSelect}
      className={`group relative p-3 rounded-lg cursor-pointer transition-all duration-150 ${
        isSelected
          ? 'bg-primary/10 border border-primary/30 pl-4 border-l-2 border-l-primary'
          : 'hover:bg-accent border border-transparent pl-4'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-foreground truncate">{conversation.title}</h4>
          <p className="text-xs text-muted-foreground mt-1">
            {conversation.message_count} {conversation.message_count === 1 ? 'message' : 'messages'}
          </p>
          <p className="text-xs text-muted-foreground">
            {new Date(conversation.updated_at).toLocaleDateString()}
          </p>
        </div>

        <button
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/10 rounded transition-opacity disabled:opacity-50"
        >
          <Trash2 className="w-4 h-4 text-red-500" />
        </button>
      </div>
    </div>
  )
}
