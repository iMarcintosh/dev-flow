import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  X, Edit2, BarChart3, Wrench, ScrollText, Clock, CheckCircle2, XCircle, Loader2, Calendar,
  MessageSquare, Search, Code, FileText, Trello, Cloud, Plug,
} from 'lucide-react'
import type { CustomAgent, AgentConversation } from '@/types/custom-agent'
import { getAgentSummary, getAgentToolUsage, type AgentSummary, type ToolUsageStat } from '@/services/analytics'
import { scheduledRunsService, type ScheduledRun } from '@/services/scheduledRuns'
import { getAgentConversations } from '@/services/custom-agents'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface AgentDetailsModalProps {
  agent: CustomAgent
  onClose: () => void
  onEdit: () => void
}

type TabType = 'overview' | 'analytics' | 'tools' | 'activity' | 'scheduled'

// Tool icon mapping — covers both enabled_tools IDs and backend tool_name values
const TOOL_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  // Tool-IDs (from enabled_tools / AVAILABLE_TOOLS)
  web_search: Search,
  code_execution: Code,
  knowledge_base: FileText,
  board: Trello,
  weather: Cloud,
  mcp: Plug,
  // Backend tool_name values (from ToolUsageLog)
  get_weather: Cloud,
  execute_code: Code,
  search_knowledge_base: FileText,
  read_url: Search,
  create_task: Trello,
  update_status: Trello,
  add_comment: Trello,
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_weather: 'Weather',
  execute_code: 'Code Execution',
  search_knowledge_base: 'Knowledge Base',
  read_url: 'Web Search',
  web_search: 'Web Search',
  create_task: 'Board: Create Task',
  update_status: 'Board: Update Status',
  add_comment: 'Board: Add Comment',
}

const getToolDisplayName = (name: string) =>
  TOOL_DISPLAY_NAMES[name] ?? name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

type ConversationTimelineItem = {
  kind: 'conversation'
  id: string
  sortDate: string
  conversation: AgentConversation
}
type ScheduledRunTimelineItem = {
  kind: 'scheduled_run'
  id: string
  sortDate: string
  run: ScheduledRun
}
type ActivityTimelineItem = ConversationTimelineItem | ScheduledRunTimelineItem

export function AgentDetailsModal({ agent, onClose, onEdit }: AgentDetailsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [timeRange, setTimeRange] = useState(30)

  // Fetch analytics data
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['agent-summary', agent.id, timeRange],
    queryFn: () => getAgentSummary(agent.id, timeRange),
  })

  const { data: toolUsage = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['agent-tools', agent.id, timeRange],
    queryFn: () => getAgentToolUsage(agent.id, timeRange),
  })

  const { data: conversations = [], isLoading: conversationsLoading } = useQuery({
    queryKey: ['agent-conversations', agent.id],
    queryFn: () => getAgentConversations(agent.id, 20),
    enabled: activeTab === 'activity',
  })

  const { data: activityScheduledRuns = [], isLoading: activityRunsLoading } = useQuery({
    queryKey: ['activity-scheduled-runs', agent.id],
    queryFn: () => scheduledRunsService.getScheduledRuns(agent.id, 20),
    enabled: activeTab === 'activity',
  })

  const { data: scheduledRuns = [], isLoading: scheduledRunsLoading } = useQuery({
    queryKey: ['scheduled-runs', agent.id],
    queryFn: () => scheduledRunsService.getScheduledRuns(agent.id, 20),
    enabled: activeTab === 'scheduled',
  })

  const tabs = [
    { id: 'overview' as TabType, label: 'Overview', icon: BarChart3 },
    { id: 'analytics' as TabType, label: 'Analytics', icon: BarChart3 },
    { id: 'tools' as TabType, label: 'Tool Usage', icon: Wrench },
    { id: 'activity' as TabType, label: 'Activity Log', icon: ScrollText },
    ...(agent.trigger === 'scheduled' ? [{ id: 'scheduled' as TabType, label: 'Scheduled Runs', icon: Calendar }] : []),
  ]

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg max-w-4xl w-full h-[85vh] flex flex-col shadow-xl">{/* Fixed height */}
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{agent.icon}</span>
            <div>
              <h2 className="text-lg font-bold text-foreground">{agent.name}</h2>
              <p className="text-sm text-muted-foreground">{agent.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onEdit}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Edit agent"
            >
              <Edit2 className="w-5 h-5 text-muted-foreground" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-border flex-shrink-0">
          <div className="flex px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && <OverviewTab agent={agent} />}
          {activeTab === 'analytics' && (
            <AnalyticsTab
              summary={summary}
              isLoading={summaryLoading}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
            />
          )}
          {activeTab === 'tools' && (
            <ToolUsageTab toolUsage={toolUsage} isLoading={toolsLoading} enabledTools={agent.enabled_tools} />
          )}
          {activeTab === 'activity' && (
            <ActivityLogTab
              conversations={conversations}
              scheduledRuns={activityScheduledRuns}
              isLoading={conversationsLoading || activityRunsLoading}
            />
          )}
          {activeTab === 'scheduled' && (
            <ScheduledRunsTab runs={scheduledRuns} isLoading={scheduledRunsLoading} />
          )}
        </div>
      </div>
    </div>
  )
}

// Overview Tab Component
function OverviewTab({ agent }: { agent: CustomAgent }) {
  const visibilityBadge = {
    private: { label: 'Private', color: 'bg-gray-500/10 text-gray-500' },
    team: { label: 'Team', color: 'bg-blue-500/10 text-blue-500' },
    public: { label: 'Public', color: 'bg-green-500/10 text-green-500' },
  }[agent.visibility]

  return (
    <div className="space-y-6">
      {/* Agent Info */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Agent Information</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Visibility</span>
            <span className={`text-xs px-2 py-1 rounded ${visibilityBadge.color}`}>
              {visibilityBadge.label}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Model</span>
            <span className="text-sm text-foreground font-mono">{agent.model_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Created</span>
            <span className="text-sm text-foreground">
              {new Date(agent.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Updated</span>
            <span className="text-sm text-foreground">
              {new Date(agent.updated_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Configuration</h3>
        <div className="space-y-3">
          <div>
            <label className="text-sm text-muted-foreground">System Prompt</label>
            <div className="mt-1 p-3 bg-background border border-border rounded-lg max-h-32 overflow-y-auto text-sm text-foreground">
              {agent.system_prompt}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-sm text-muted-foreground">Temperature</label>
              <div className="mt-1 text-sm text-foreground font-mono">{agent.temperature}</div>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Max Tokens</label>
              <div className="mt-1 text-sm text-foreground font-mono">{agent.max_tokens}</div>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Top P</label>
              <div className="mt-1 text-sm text-foreground font-mono">{agent.top_p}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Enabled Tools */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">
          Enabled Tools ({agent.enabled_tools.length})
        </h3>
        <div className="flex flex-wrap gap-2">
          {agent.enabled_tools.length > 0 ? (
            agent.enabled_tools.map((tool) => (
              <span
                key={tool}
                className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
              >
                {tool}
              </span>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No tools enabled</p>
          )}
        </div>
      </div>
    </div>
  )
}

// Analytics Tab Component
function AnalyticsTab({
  summary,
  isLoading,
  timeRange,
  onTimeRangeChange
}: {
  summary: AgentSummary | null | undefined
  isLoading: boolean
  timeRange: number
  onTimeRangeChange: (days: number) => void
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
        <p className="text-muted-foreground">No analytics data yet</p>
        <p className="text-sm text-muted-foreground mt-1">
          Start using this agent to see analytics
        </p>
      </div>
    )
  }

  const successRate = summary.success_rate || 0

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-end gap-2">
        {[7, 30, 90].map((days) => (
          <button
            key={days}
            onClick={() => onTimeRangeChange(days)}
            className={`px-3 py-1 text-sm rounded-lg transition-colors ${
              timeRange === days
                ? 'bg-primary text-primary-foreground'
                : 'bg-background border border-border text-foreground hover:bg-accent'
            }`}
          >
            {days}d
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-background border border-border rounded-lg">
          <div className="text-sm text-muted-foreground mb-1">Total Runs</div>
          <div className="text-2xl font-bold text-foreground">{summary.total_runs}</div>
          <div className="mt-2 flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1 text-green-500">
              <CheckCircle2 className="w-3 h-3" />
              {summary.successful_runs} success
            </div>
            <div className="flex items-center gap-1 text-red-500">
              <XCircle className="w-3 h-3" />
              {summary.failed_runs} failed
            </div>
          </div>
        </div>

        <div className="p-4 bg-background border border-border rounded-lg">
          <div className="text-sm text-muted-foreground mb-1">Success Rate</div>
          <div className="text-2xl font-bold text-foreground">{successRate.toFixed(1)}%</div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                successRate >= 90 ? 'bg-green-500' : successRate >= 70 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${successRate}%` }}
            />
          </div>
        </div>

        <div className="p-4 bg-background border border-border rounded-lg">
          <div className="text-sm text-muted-foreground mb-1">Avg Response Time</div>
          <div className="text-2xl font-bold text-foreground">
            {summary.avg_response_time?.toFixed(2) || 0}s
          </div>
          {summary.min_response_time !== undefined && summary.max_response_time !== undefined && (
            <div className="mt-2 text-xs text-muted-foreground">
              Min: {summary.min_response_time.toFixed(2)}s • Max: {summary.max_response_time.toFixed(2)}s
            </div>
          )}
        </div>

        <div className="p-4 bg-background border border-border rounded-lg">
          <div className="text-sm text-muted-foreground mb-1">Total Tokens</div>
          <div className="text-2xl font-bold text-foreground">
            {(summary.total_tokens || 0).toLocaleString()}
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Prompt: {(summary.prompt_tokens || 0).toLocaleString()} •{' '}
            Completion: {(summary.completion_tokens || 0).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Tool Calls */}
      {(summary.tool_calls_count || 0) > 0 && (
        <div className="p-4 bg-background border border-border rounded-lg">
          <div className="text-sm text-muted-foreground mb-1">Tool Calls</div>
          <div className="text-2xl font-bold text-foreground">{summary.tool_calls_count || 0}</div>
        </div>
      )}
    </div>
  )
}

// Tool Usage Tab Component
function ToolUsageTab({
  toolUsage,
  isLoading,
  enabledTools,
}: {
  toolUsage: ToolUsageStat[]
  isLoading: boolean
  enabledTools: string[]
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  if (toolUsage.length === 0) {
    if (enabledTools.length > 0) {
      return (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground mb-4">
            No usage data yet. These tools are configured for this agent:
          </p>
          {enabledTools.map((toolName) => {
            const Icon = TOOL_ICONS[toolName] || Wrench
            return (
              <div
                key={toolName}
                className="p-4 bg-background border border-border rounded-lg flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="font-medium text-foreground">{getToolDisplayName(toolName)}</span>
                </div>
                <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                  Not used yet
                </span>
              </div>
            )
          })}
        </div>
      )
    }
    return (
      <div className="text-center py-12">
        <Wrench className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
        <p className="text-muted-foreground">No tool usage data yet</p>
      </div>
    )
  }

  // Sort by usage count
  const sortedTools = [...toolUsage].sort((a, b) => b.usage_count - a.usage_count)

  return (
    <div className="space-y-4">
      {sortedTools.map((tool) => (
        <div key={tool.tool_name} className="p-4 bg-background border border-border rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium text-foreground">{getToolDisplayName(tool.tool_name)}</div>
            <div className="text-sm text-muted-foreground">{tool.usage_count} uses</div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>Success Rate</span>
                <span>{tool.success_rate.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${tool.success_rate}%` }}
                />
              </div>
            </div>

            {tool.avg_execution_time && (
              <div className="text-sm text-muted-foreground whitespace-nowrap">
                {tool.avg_execution_time.toFixed(2)}s avg
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

// Activity Log Tab Component
function ActivityLogTab({
  conversations,
  scheduledRuns,
  isLoading,
}: {
  conversations: AgentConversation[]
  scheduledRuns: ScheduledRun[]
  isLoading: boolean
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  if (conversations.length === 0 && scheduledRuns.length === 0) {
    return (
      <div className="text-center py-12">
        <ScrollText className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
        <p className="text-muted-foreground">No activity yet</p>
        <p className="text-sm text-muted-foreground mt-1">
          Chat with this agent or run it on a schedule to see activity here
        </p>
      </div>
    )
  }

  // Merge and sort timeline items
  const timeline: ActivityTimelineItem[] = [
    ...conversations.map((conv): ConversationTimelineItem => ({
      kind: 'conversation',
      id: conv.id,
      sortDate: conv.updated_at,
      conversation: conv,
    })),
    ...scheduledRuns.map((run): ScheduledRunTimelineItem => ({
      kind: 'scheduled_run',
      id: run.id,
      sortDate: run.executed_at,
      run,
    })),
  ].sort((a, b) => new Date(b.sortDate).getTime() - new Date(a.sortDate).getTime())

  return (
    <div className="space-y-2">
      {timeline.map((item) => {
        if (item.kind === 'conversation') {
          const conv = item.conversation
          return (
            <div
              key={`conv-${item.id}`}
              className="border border-border rounded-lg p-4 flex items-center justify-between gap-4 hover:border-blue-500/50 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-blue-500/10 text-blue-500 flex-shrink-0">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-medium text-blue-500">CONVERSATION</span>
                  </div>
                  <p className="text-sm text-foreground truncate">
                    {conv.title || 'Untitled conversation'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                  {conv.message_count} messages
                </span>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  {new Date(conv.updated_at).toLocaleString()}
                </div>
              </div>
            </div>
          )
        }

        // scheduled_run
        const run = item.run
        const isExpanded = expandedId === `run-${run.id}`
        const isSuccess = run.status === 'success'
        const StatusIcon = isSuccess ? CheckCircle2 : XCircle
        const statusColor = isSuccess ? 'text-green-500' : 'text-red-500'

        return (
          <div
            key={`run-${item.id}`}
            className="border border-border rounded-lg overflow-hidden hover:border-primary/50 transition-colors"
          >
            <div
              className="p-4 cursor-pointer flex items-center justify-between gap-4"
              onClick={() => setExpandedId(isExpanded ? null : `run-${run.id}`)}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <StatusIcon className={`w-4 h-4 flex-shrink-0 ${statusColor}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`text-xs font-medium ${statusColor}`}>SCHEDULED RUN</span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(run.executed_at).toLocaleString()}
                    </span>
                  </div>
                  {run.response && (
                    <p className="text-sm text-foreground truncate">
                      {run.response.substring(0, 120)}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {run.response_time != null && (
                  <span className="text-xs text-muted-foreground">{run.response_time.toFixed(2)}s</span>
                )}
                {run.tools_used != null && run.tools_used > 0 && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Wrench className="w-3 h-3" />
                    {run.tools_used}
                  </div>
                )}
              </div>
            </div>

            {isExpanded && (
              <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
                {run.input_text && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">Input:</div>
                    <div className="text-xs bg-background p-3 rounded border border-border">
                      {run.input_text}
                    </div>
                  </div>
                )}
                {run.response && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">Response:</div>
                    <div className="text-xs bg-background p-3 rounded border border-border">
                      <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-headings:my-2 prose-pre:my-1 prose-ul:my-1 prose-ol:my-1">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{run.response}</ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}
                {run.error && (
                  <div>
                    <div className="text-xs font-semibold text-red-500 mb-1">Error:</div>
                    <div className="text-xs text-red-500 bg-red-500/10 p-3 rounded">
                      {run.error}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// Scheduled Runs Tab Component
function ScheduledRunsTab({
  runs,
  isLoading
}: {
  runs: ScheduledRun[]
  isLoading: boolean
}) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <Calendar className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
        <p className="text-muted-foreground mb-2">No scheduled runs yet</p>
        <p className="text-sm text-muted-foreground/70">
          This agent hasn't executed any scheduled runs
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {runs.map((run) => {
        const isExpanded = expandedId === run.id
        const statusColor = run.status === 'success' ? 'text-green-500' : 'text-red-500'
        const StatusIcon = run.status === 'success' ? CheckCircle2 : XCircle

        return (
          <div
            key={run.id}
            className="border border-border rounded-lg overflow-hidden hover:border-primary/50 transition-colors"
          >
            <div
              className="p-4 cursor-pointer flex items-center justify-between gap-4"
              onClick={() => setExpandedId(isExpanded ? null : run.id)}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <StatusIcon className={`w-4 h-4 flex-shrink-0 ${statusColor}`} />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <span className={`text-xs font-medium ${statusColor}`}>
                      {run.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(run.executed_at).toLocaleString()}
                    </span>
                  </div>

                  {run.response && (
                    <p className="text-sm text-foreground truncate">
                      {run.response.substring(0, 100)}...
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-4 flex-shrink-0">
                {run.response_time != null && (
                  <div className="text-xs text-muted-foreground">
                    {run.response_time.toFixed(2)}s
                  </div>
                )}
                {run.tools_used != null && run.tools_used > 0 && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Wrench className="w-3 h-3" />
                    {run.tools_used}
                  </div>
                )}
              </div>
            </div>

            {isExpanded && (
              <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
                {run.input_text && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">Input:</div>
                    <div className="text-xs bg-background p-3 rounded border border-border">
                      {run.input_text}
                    </div>
                  </div>
                )}

                {run.response && (
                  <div>
                    <div className="text-xs font-semibold text-muted-foreground mb-1">Response:</div>
                    <div className="text-xs bg-background p-3 rounded border border-border">
                      <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-headings:my-2 prose-pre:my-1 prose-ul:my-1 prose-ol:my-1">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {run.response}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}

                {run.error && (
                  <div>
                    <div className="text-xs font-semibold text-red-500 mb-1">Error:</div>
                    <div className="text-xs text-red-500 bg-red-500/10 p-3 rounded">
                      {run.error}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
