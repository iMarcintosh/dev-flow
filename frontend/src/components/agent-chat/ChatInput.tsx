import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface ChatInputProps {
  conversationId: string
  onError?: (hasError: boolean) => void
  isStreaming?: boolean
  onSendMessage?: (text: string) => void
}

export function ChatInput({ onError, isStreaming, onSendMessage }: ChatInputProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    const text = message.trim()
    if (!text || isStreaming) return
    onSendMessage?.(text)
    setMessage('')
    onError?.(false)
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
          onChange={(e) => {
            setMessage(e.target.value)
            onError?.(false)
          }}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          disabled={isStreaming}
          rows={3}
          className="flex-1 px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 resize-none"
        />
        <button
          onClick={handleSend}
          disabled={!message.trim() || isStreaming}
          className="self-end px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isStreaming ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  )
}
