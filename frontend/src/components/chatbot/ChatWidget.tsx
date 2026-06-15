import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Trash2 } from 'lucide-react'
import { useChatHistory, useProjectItems, useClearChatHistory } from '@/services/queries'
import { useQueryClient } from '@tanstack/react-query'
import type { ChatMessage } from '@/types/chat'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ChatWidgetProps {
  projectId: string
}

export default function ChatWidget({ projectId }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [optimisticUserMessage, setOptimisticUserMessage] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data: history = [] } = useChatHistory(isOpen ? projectId : undefined)
  const { data: items = [] } = useProjectItems(isOpen ? projectId : undefined)
  const clearMutation = useClearChatHistory(projectId)

  const handleClearHistory = () => {
    if (!confirm('Clear all chat history for this project?')) return
    clearMutation.mutate()
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [history, streamingContent])

  const handleSend = async () => {
    if (!message.trim() || isStreaming) return

    const text = message.trim()
    setMessage('')
    setIsStreaming(true)
    setStreamingContent('')
    setOptimisticUserMessage(text)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ project_id: projectId, message: text }),
      })

      if (!response.ok || !response.body) {
        throw new Error(`Request failed: ${response.status}`)
      }

      const reader = response.body.getReader()
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
            } else if (event.type === 'end') {
              setIsStreaming(false)
              setStreamingContent('')
              setOptimisticUserMessage(null)
              queryClient.invalidateQueries({ queryKey: ['chat', projectId] })
            } else if (event.type === 'error') {
              setStreamingContent(event.content || 'An error occurred.')
              setIsStreaming(false)
              setOptimisticUserMessage(null)
              queryClient.invalidateQueries({ queryKey: ['chat', projectId] })
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch (err) {
      console.error('Chat stream error:', err)
      setStreamingContent('Failed to connect. Please try again.')
    } finally {
      setIsStreaming(false)
      setOptimisticUserMessage(null)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-indigo-600 hover:bg-indigo-700 rounded-full shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110 z-50"
      >
        <MessageCircle className="w-6 h-6 text-white" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-gray-900 border border-gray-800 rounded-lg shadow-2xl flex flex-col z-50 animate-in slide-in-from-bottom-4 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-indigo-500" />
          <h3 className="font-semibold text-white">DevFlow Assistant</h3>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleClearHistory}
            disabled={isStreaming || clearMutation.isPending}
            title="Clear chat history"
            className="text-gray-400 hover:text-red-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Context Indicator */}
      <div className="px-4 py-2 bg-gray-800/50 border-b border-gray-800">
        <p className="text-xs text-gray-400">
          Tracking {items.length} {items.length === 1 ? 'item' : 'items'} in this project
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {history.length === 0 && !isStreaming && (
          <div className="text-center text-gray-500 mt-8">
            <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">Ask me anything about your board!</p>
            <p className="text-xs mt-2">
              Try: "How many bugs do we have?" or "What's our status?"
            </p>
          </div>
        )}

        {history.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* Optimistic user message */}
        {optimisticUserMessage && (
          <div className="flex justify-end">
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-indigo-600 text-white">
              <p className="text-sm whitespace-pre-wrap">{optimisticUserMessage}</p>
            </div>
          </div>
        )}

        {/* Streaming bubble */}
        {isStreaming && !streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] bg-gray-800 rounded-lg px-4 py-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        {isStreaming && streamingContent && (
          <div className="flex justify-start">
            <div className="max-w-[80%] bg-gray-800 rounded-lg px-4 py-2">
              <p className="text-sm text-gray-100 whitespace-pre-wrap">
                {streamingContent}
                <span className="inline-block w-0.5 h-3.5 bg-gray-400 animate-pulse ml-0.5 align-middle" />
              </p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your board..."
            disabled={isStreaming}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!message.trim() || isStreaming}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-800 text-gray-100'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <p className={`text-xs mt-1 ${isUser ? 'text-indigo-200' : 'text-gray-500'}`}>
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}
