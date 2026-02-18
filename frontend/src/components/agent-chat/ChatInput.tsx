import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Loader2 } from 'lucide-react'
import { conversationService } from '@/services/custom-agents'

interface ChatInputProps {
  conversationId: string
}

export function ChatInput({ conversationId }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const queryClient = useQueryClient()

  const sendMutation = useMutation({
    mutationFn: (text: string) => conversationService.sendMessage(conversationId, text),
    onSuccess: (data) => {
      // Check if backend returned an error
      if (!data.success && data.error) {
        // Don't clear message on error, show error to user
        return
      }
      
      // Success - invalidate queries and clear input
      queryClient.invalidateQueries({ queryKey: ['conversation-messages', conversationId] })
      queryClient.invalidateQueries({ queryKey: ['agent-conversations'] })
      setMessage('')
    },
    onError: (error) => {
      // Network or other errors - handled by error display below
      console.error('Failed to send message:', error)
    },
  })

  const handleSend = () => {
    if (!message.trim() || sendMutation.isPending) return
    sendMutation.mutate(message)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t border-border bg-card p-4">
      <div className="flex gap-3">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          disabled={sendMutation.isPending}
          rows={3}
          className="flex-1 px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 resize-none"
        />
        <button
          onClick={handleSend}
          disabled={!message.trim() || sendMutation.isPending}
          className="self-end px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {sendMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>

      {sendMutation.isError && (
        <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400 font-medium">Failed to send message</p>
          {sendMutation.error && (
            <p className="text-xs text-red-500 dark:text-red-400 mt-1">
              {(sendMutation.error as any)?.response?.data?.error || 
               (sendMutation.error as any)?.message || 
               'Please try again.'}
            </p>
          )}
        </div>
      )}
      
      {/* Backend error (success: false) */}
      {sendMutation.isSuccess && sendMutation.data && !sendMutation.data.success && sendMutation.data.error && (
        <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400 font-medium">Agent Error</p>
          <p className="text-xs text-red-500 dark:text-red-400 mt-1 font-mono">
            {sendMutation.data.error}
          </p>
        </div>
      )}
    </div>
  )
}
