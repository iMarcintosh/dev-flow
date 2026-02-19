import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { Loader2, Bot, User, Check, Loader } from 'lucide-react'
import { conversationService } from '@/services/custom-agents'
import type { AgentMessage } from '@/types/custom-agent'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'

const TOOL_ICONS: Record<string, string> = {
  web_search: '🔍',
  code_execution: '💻',
  knowledge_base: '📚',
  weather: '🌤',
  board: '📋',
}

interface ActiveTool {
  name: string
  done: boolean
  duration_ms?: number
}

interface MessageListProps {
  conversationId: string
  agentId: string
  hasError?: boolean
  isStreaming?: boolean
  streamingContent?: string
  activeTools?: ActiveTool[]
}

export function MessageList({
  conversationId,
  hasError,
  isStreaming,
  streamingContent,
  activeTools = [],
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: messages = [], isLoading } = useQuery({
    queryKey: ['conversation-messages', conversationId],
    queryFn: () => conversationService.getMessages(conversationId),
    // No refetchInterval — streaming handles real-time updates
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, isStreaming])

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {messages.length === 0 && !isStreaming && (
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

      {/* Streaming bubble */}
      {isStreaming && (
        <StreamingMessageBubble content={streamingContent ?? ''} activeTools={activeTools} />
      )}

      {hasError && !isStreaming && (
        <div className="flex gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-accent">
            <Bot className="w-4 h-4 text-foreground" />
          </div>
          <div className="flex-1 max-w-[70%]">
            <div className="rounded-lg px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-600 dark:text-red-400">
                An error occurred. Please try again.
              </p>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

interface MessageBubbleProps {
  message: AgentMessage
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
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
                remarkPlugins={[remarkGfm]}
                components={{
                  table({ children }) {
                    return (
                      <div className="my-4 overflow-x-auto">
                        <table className="min-w-full divide-y divide-border border border-border rounded-lg">
                          {children}
                        </table>
                      </div>
                    )
                  },
                  thead({ children }) {
                    return <thead className="bg-muted">{children}</thead>
                  },
                  th({ children }) {
                    return (
                      <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        {children}
                      </th>
                    )
                  },
                  td({ children }) {
                    return (
                      <td className="px-4 py-2 text-sm text-foreground border-t border-border">
                        {children}
                      </td>
                    )
                  },
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const codeString = String(children).replace(/\n$/, '')

                    return !inline && language ? (
                      <div className="my-4 rounded-lg overflow-hidden border border-border">
                        <div className="flex items-center justify-between px-4 py-2 bg-muted border-b border-border">
                          <span className="text-xs font-medium text-muted-foreground uppercase">
                            {language}
                          </span>
                        </div>
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

interface StreamingMessageBubbleProps {
  content: string
  activeTools: ActiveTool[]
}

function StreamingMessageBubble({ content, activeTools }: StreamingMessageBubbleProps) {
  const showThinking = activeTools.length === 0 && !content

  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-accent">
        <Bot className="w-4 h-4 text-foreground" />
      </div>

      <div className="flex-1 max-w-[70%] flex flex-col">
        <div className="rounded-lg px-4 py-3 bg-card border border-border text-foreground">
          {/* Tool badges */}
          {activeTools.length > 0 && (
            <div className="space-y-1.5 mb-3">
              {activeTools.map((tool, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  {tool.done ? (
                    <Check className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  ) : (
                    <Loader className="w-3.5 h-3.5 text-primary animate-spin flex-shrink-0" />
                  )}
                  <span className="mr-1">{TOOL_ICONS[tool.name] ?? '🔧'}</span>
                  <span className={tool.done ? 'text-muted-foreground' : 'text-foreground'}>
                    {tool.done ? tool.name : `${tool.name}...`}
                  </span>
                  {tool.done && tool.duration_ms !== undefined && (
                    <span className="text-xs text-muted-foreground ml-1">
                      {(tool.duration_ms / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Streaming text or thinking indicator */}
          {content ? (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              <span className="inline-block w-0.5 h-4 bg-primary animate-pulse ml-0.5 align-middle" />
            </div>
          ) : showThinking ? (
            <div className="flex gap-1.5 items-center">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]" />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]" />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
            </div>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground mt-1">Thinking...</p>
      </div>
    </div>
  )
}
