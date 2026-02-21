import { useState } from 'react'
import { Send, Square } from 'lucide-react'

interface ChatInputProps {
  conversationId: string
  onError?: (hasError: boolean) => void
  isStreaming?: boolean
  onSendMessage?: (text: string) => void
  onStop?: () => void
}

export function ChatInput({ onError, isStreaming, onSendMessage, onStop }: ChatInputProps) {
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
          className="flex-1 px-4 py-3 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.12)] transition-all duration-200 disabled:opacity-50 resize-none"
        />
        {isStreaming ? (
          <button
            onClick={onStop}
            className="self-end px-4 py-3 bg-red-500/15 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/25 transition-all duration-150 active:scale-95"
          >
            <Square className="w-5 h-5" fill="currentColor" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!message.trim()}
            className="self-end px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all duration-150 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  )
}
