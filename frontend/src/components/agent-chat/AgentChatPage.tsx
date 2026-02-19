import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { conversationService, customAgentService } from '@/services/custom-agents'
import { ConversationList } from './ConversationList'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AgentChatPage() {
  const navigate = useNavigate()
  const search = useSearch({ from: '/chat' })
  const queryClient = useQueryClient()

  const agentId = (search as any).agent_id as string | undefined
  const conversationIdFromUrl = (search as any).conversation_id as string | undefined

  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>(
    conversationIdFromUrl
  )
  const [chatError, setChatError] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [activeTools, setActiveTools] = useState<Array<{ name: string; done: boolean; duration_ms?: number }>>([])
  const abortRef = useRef<AbortController | null>(null)

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
    setChatError(false)
  }

  const handleDeleteConversation = (conversationId: string) => {
    if (conversationId === selectedConversationId) {
      const otherConversations = conversations.filter((c) => c.id !== conversationId)
      setSelectedConversationId(otherConversations[0]?.id)
    }
    queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] })
  }

  const sendMessage = async (text: string) => {
    if (!selectedConversationId || isStreaming) return

    // Cancel any in-progress stream
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setIsStreaming(true)
    setStreamingContent('')
    setActiveTools([])
    setChatError(false)

    try {
      const token = localStorage.getItem('access_token')
      const url = `${API_URL}/api/agent-chat/conversations/${selectedConversationId}/messages/stream?message=${encodeURIComponent(text)}`
      const response = await fetch(url, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))

            if (event.type === 'stream') {
              setStreamingContent((prev) => prev + event.content)
            } else if (event.type === 'tool_call') {
              setActiveTools((prev) => [...prev, { name: event.name, done: false }])
            } else if (event.type === 'tool_result') {
              setActiveTools((prev) =>
                prev.map((t) =>
                  t.name === event.name && !t.done
                    ? { ...t, done: true, duration_ms: event.duration_ms }
                    : t
                )
              )
            } else if (event.type === 'end') {
              setIsStreaming(false)
              setStreamingContent('')
              setActiveTools([])
              queryClient.invalidateQueries({
                queryKey: ['conversation-messages', selectedConversationId],
              })
              queryClient.invalidateQueries({ queryKey: ['agent-conversations', agentId] })
            } else if (event.type === 'error') {
              setIsStreaming(false)
              setChatError(true)
            }
          } catch {
            // malformed JSON chunk — skip
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Streaming error:', err)
        setChatError(true)
      }
      setIsStreaming(false)
    }
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
                <MessageList
                  conversationId={selectedConversation.id}
                  agentId={agentId}
                  hasError={chatError}
                  isStreaming={isStreaming}
                  streamingContent={streamingContent}
                  activeTools={activeTools}
                />
                <ChatInput
                  conversationId={selectedConversation.id}
                  onError={setChatError}
                  isStreaming={isStreaming}
                  onSendMessage={sendMessage}
                />
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
