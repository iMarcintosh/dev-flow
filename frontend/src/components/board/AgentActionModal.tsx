import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Send, Loader2, Bot } from 'lucide-react'
import api from '@/services/api'
import type { Item } from '@/types'
import ReactMarkdown from 'react-markdown'

interface AgentActionModalProps {
  item: Item
  agentId: string
  onClose: () => void
}

export function AgentActionModal({ item, agentId, onClose }: AgentActionModalProps) {
  const [message, setMessage] = useState('')
  const [response, setResponse] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const actionMutation = useMutation({
    mutationFn: (msg: string) =>
      api.post(`/api/items/${item.id}/agent-action`, { message: msg }),
    onSuccess: (data) => {
      setResponse(data.data.agent_response)
      queryClient.invalidateQueries({ queryKey: ['project-items'] })
    },
  })

  const handleSend = () => {
    if (!message.trim() || actionMutation.isPending) return
    actionMutation.mutate(message)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="w-5 h-5 text-primary" />
            <div>
              <h2 className="text-lg font-bold text-foreground">Ask Agent</h2>
              <p className="text-sm text-muted-foreground">{item.title}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {response ? (
            <div className="space-y-4">
              {/* User Message */}
              <div className="flex justify-end">
                <div className="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
                  <p className="text-sm">{message}</p>
                </div>
              </div>

              {/* Agent Response */}
              <div className="flex justify-start">
                <div className="bg-accent rounded-lg px-4 py-3 max-w-[80%]">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{response}</ReactMarkdown>
                  </div>
                </div>
              </div>

              {/* Ask Another Question */}
              <div className="pt-4 border-t border-border">
                <button
                  onClick={() => {
                    setResponse(null)
                    setMessage('')
                  }}
                  className="text-sm text-primary hover:text-primary/80"
                >
                  Ask another question
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  What would you like the agent to help with?
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g., 'What steps should I take to fix this bug?' or 'Break this epic into smaller tasks'"
                  rows={4}
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              <div className="bg-accent/50 border border-border rounded-lg p-3">
                <p className="text-xs text-muted-foreground">
                  <strong>Context provided to agent:</strong>
                  <br />
                  Title: {item.title}
                  <br />
                  Status: {item.status} • Priority: {item.priority} • Type: {item.type}
                </p>
              </div>
            </div>
          )}

          {actionMutation.isError && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-sm text-red-500">Failed to get agent response. Please try again.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        {!response && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-foreground hover:bg-accent rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSend}
              disabled={!message.trim() || actionMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {actionMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Asking...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Ask Agent
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
