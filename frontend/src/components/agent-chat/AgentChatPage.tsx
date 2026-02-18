import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { conversationService, customAgentService } from '@/services/custom-agents'
import { ConversationList } from './ConversationList'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'

export default function AgentChatPage() {
  const navigate = useNavigate()
  const search = useSearch({ from: '/chat' })
  const queryClient = useQueryClient()

  const agentId = (search as any).agent_id as string | undefined
  const conversationIdFromUrl = (search as any).conversation_id as string | undefined

  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>(
    conversationIdFromUrl
  )

  const { data: agent, isLoading: agentLoading } = useQuery({
    queryKey: ['custom-agent', agentId],
    queryFn: () => customAgentService.getAgent(agentId!),
    enabled: !!agentId,
  })

  const { data: conversations = [], isLoading: conversationsLoading } = useQuery({
    queryKey: ['agent-conversations', agentId],
    queryFn: () => conversationService.listConversations(agentId),
    enabled: !!agentId,
  })

  useEffect(() => {
    if (!selectedConversationId && conversations.length > 0) {
      setSelectedConversationId(conversations[0].id)
    }
  }, [conversations, selectedConversationId])

  const createConversationMutation = useMutation({
    mutationFn: () => conversationService.createConversation(agentId!),
    onSuccess: (newConversation) => {
      queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] })
      setSelectedConversationId(newConversation.id)
    },
  })

  const selectedConversation = conversations.find((c) => c.id === selectedConversationId)

  const handleNewConversation = () => {
    createConversationMutation.mutate()
  }

  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversationId(conversationId)
  }

  const handleDeleteConversation = (conversationId: string) => {
    if (conversationId === selectedConversationId) {
      const otherConversations = conversations.filter((c) => c.id !== conversationId)
      setSelectedConversationId(otherConversations[0]?.id)
    }
    queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] })
  }

  if (!agentId) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground">No agent selected</p>
            <button
              onClick={() => navigate({ to: '/agents' })}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Go to Agent Hub
            </button>
          </div>
        </div>
      </AppLayout>
    )
  }

  if (agentLoading || conversationsLoading) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </AppLayout>
    )
  }

  if (!agent) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground">Agent not found</p>
            <button
              onClick={() => navigate({ to: '/agents' })}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Go to Agent Hub
            </button>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="h-screen bg-background flex flex-col">
        <div className="border-b border-border bg-card px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate({ to: '/agents' })}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <span className="text-3xl">{agent.icon}</span>
              <div>
                <h1 className="text-xl font-bold text-foreground">{agent.name}</h1>
                <p className="text-sm text-muted-foreground">{agent.description}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <ConversationList
            conversations={conversations}
            selectedId={selectedConversationId}
            onSelect={handleSelectConversation}
            onNew={handleNewConversation}
            onDelete={handleDeleteConversation}
            isCreating={createConversationMutation.isPending}
          />

          <div className="flex-1 flex flex-col">
            {selectedConversation ? (
              <>
                <MessageList conversationId={selectedConversation.id} agentId={agentId} />
                <ChatInput conversationId={selectedConversation.id} />
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-muted-foreground mb-4">No conversation selected</p>
                  <button
                    onClick={handleNewConversation}
                    disabled={createConversationMutation.isPending}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                  >
                    {createConversationMutation.isPending ? 'Creating...' : 'Start New Conversation'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
