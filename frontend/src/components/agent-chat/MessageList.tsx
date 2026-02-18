import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Loader2, Bot, User } from 'lucide-react'
import { conversationService } from '@/services/custom-agents'
import type { AgentMessage } from '@/types/custom-agent'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface MessageListProps {
  conversationId: string
  agentId: string
}

export function MessageList({ conversationId }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isThinking, setIsThinking] = useState(false)
  const prevMessageCountRef = useRef(0)

  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['conversation-messages', conversationId],
    queryFn: () => conversationService.getMessages(conversationId),
    refetchInterval: 2000, // Poll every 2 seconds for new messages
  })

  // Track if agent is thinking (user sent message but no assistant response yet)
  useEffect(() => {
    if (messages.length === 0) {
      setIsThinking(false)
      prevMessageCountRef.current = 0
      return
    }

    const lastMessage = messages[messages.length - 1]
    const isUserMessage = lastMessage.role === 'user'
    
    // If new user message was added, show thinking
    if (messages.length > prevMessageCountRef.current && isUserMessage) {
      setIsThinking(true)
    }
    
    // If assistant responded OR if there was an error, hide thinking
    if (!isUserMessage) {
      setIsThinking(false)
    }
    
    prevMessageCountRef.current = messages.length
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.length === 0 && (
        <div className="text-center py-12">
          <Bot className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-50" />
          <p className="text-muted-foreground">Start a conversation!</p>
          <p className="text-sm text-muted-foreground mt-2">
            Ask me anything or request help with your tasks.
          </p>
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Thinking indicator */}
      {isThinking && <ThinkingIndicator />}

      <div ref={messagesEndRef} />
    </div>
  )
}

interface MessageBubbleProps {
  message: AgentMessage
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  // Detect dark mode from CSS
  const [isDarkMode, setIsDarkMode] = useState(
    window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  )

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => setIsDarkMode(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary' : 'bg-accent'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-primary-foreground" />
        ) : (
          <Bot className="w-4 h-4 text-foreground" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[70%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-card border border-border text-foreground'
          }`}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const codeString = String(children).replace(/\n$/, '')
                    
                    return !inline && language ? (
                      <div className="my-4 rounded-lg overflow-hidden border border-border">
                        {/* Language label */}
                        <div className="flex items-center justify-between px-4 py-2 bg-muted border-b border-border">
                          <span className="text-xs font-medium text-muted-foreground uppercase">
                            {language}
                          </span>
                        </div>
                        {/* Code with line numbers */}
                        <SyntaxHighlighter
                          language={language}
                          style={isDarkMode ? vscDarkPlus : vs}
                          showLineNumbers
                          customStyle={{
                            margin: 0,
                            borderRadius: 0,
                            fontSize: '0.875rem',
                            padding: '1rem',
                          }}
                          lineNumberStyle={{
                            minWidth: '3em',
                            paddingRight: '1em',
                            color: isDarkMode ? '#6e7681' : '#57606a',
                            userSelect: 'none',
                          }}
                          {...props}
                        >
                          {codeString}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono" {...props}>
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <p className={`text-xs text-muted-foreground mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-accent">
        <Bot className="w-4 h-4 text-foreground" />
      </div>

      {/* Thinking animation */}
      <div className="flex-1 max-w-[70%] flex flex-col">
        <div className="rounded-lg px-4 py-3 bg-card border border-border">
          <div className="flex gap-1.5 items-center">
            <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
            <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
            <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-1">Thinking...</p>
      </div>
    </div>
  )
}
