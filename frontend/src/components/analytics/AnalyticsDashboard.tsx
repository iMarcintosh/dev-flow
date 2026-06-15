import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, CheckCircle2, XCircle, Loader2, TrendingUp } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { PageHeader } from '@/components/layout/PageHeader'
import { customAgentService } from '@/services/custom-agents'
import {
  getAgentSummary, getAgentTimeline, getAgentToolUsage,
  getGlobalSummary, getGlobalToolUsage,
} from '@/services/analytics'
import { RunsLineChart } from './RunsLineChart'
import { ToolUsageBarChart } from './ToolUsageBarChart'

const TIME_RANGES = [7, 30, 90]

export default function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState(30)
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)

  const { data: agents = [] } = useQuery({
    queryKey: ['custom-agents'],
    queryFn: () => customAgentService.listAgents(true),
  })

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary', selectedAgentId, timeRange],
    queryFn: () =>
      selectedAgentId
        ? getAgentSummary(selectedAgentId, timeRange)
        : getGlobalSummary(timeRange),
  })

  const { data: timeline = [], isLoading: timelineLoading } = useQuery({
    queryKey: ['analytics-timeline', selectedAgentId, timeRange],
    queryFn: () => getAgentTimeline(selectedAgentId!, timeRange),
    enabled: !!selectedAgentId,
  })

  const { data: toolUsage = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['analytics-tools', selectedAgentId, timeRange],
    queryFn: () =>
      selectedAgentId
        ? getAgentToolUsage(selectedAgentId, timeRange)
        : getGlobalToolUsage(timeRange),
  })

  const isLoading = summaryLoading || toolsLoading
  const successRate = summary?.success_rate ?? 0

  return (
    <AppLayout>
      <div className="flex flex-col h-full">
        <PageHeader>
          <div className="max-w-7xl mx-auto px-8 pt-6 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground">Analytics</h1>
                <p className="text-muted-foreground mt-1">Agent performance across all your agents</p>
              </div>
              <div className="flex items-center gap-2">
                {TIME_RANGES.map((days) => (
                  <button
                    key={days}
                    onClick={() => setTimeRange(days)}
                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                      timeRange === days
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-background border border-border text-foreground hover:bg-accent'
                    }`}
                  >
                    {days}d
                  </button>
                ))}
              </div>
            </div>
          </div>
        </PageHeader>

        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">

            {/* Agent Selector */}
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Agent:</span>
              <select
                value={selectedAgentId ?? ''}
                onChange={(e) => setSelectedAgentId(e.target.value || null)}
                className="px-3 py-1.5 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="">All Agents (Global)</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.icon} {a.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Loading */}
            {isLoading && (
              <div className="flex items-center justify-center min-h-[300px]">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
              </div>
            )}

            {/* No data */}
            {!isLoading && !summary && (
              <div className="flex flex-col items-center justify-center min-h-[300px] text-muted-foreground gap-3">
                <BarChart3 className="w-12 h-12" />
                <p>No analytics data yet</p>
                <p className="text-sm">Run an agent to start seeing metrics here</p>
              </div>
            )}

            {/* Content */}
            {!isLoading && summary && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-4 bg-background border border-border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Total Runs</div>
                    <div className="text-2xl font-bold text-foreground">{summary.total_runs}</div>
                    <div className="mt-2 flex items-center gap-3 text-xs">
                      <div className="flex items-center gap-1 text-green-500">
                        <CheckCircle2 className="w-3 h-3" />
                        {summary.successful_runs}
                      </div>
                      <div className="flex items-center gap-1 text-red-500">
                        <XCircle className="w-3 h-3" />
                        {summary.failed_runs}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-background border border-border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Success Rate</div>
                    <div className="text-2xl font-bold text-foreground">{successRate.toFixed(1)}%</div>
                    <div className="mt-2 w-full bg-border rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${
                          successRate >= 90 ? 'bg-green-500' : successRate >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${successRate}%` }}
                      />
                    </div>
                  </div>

                  <div className="p-4 bg-background border border-border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Avg Response Time</div>
                    <div className="text-2xl font-bold text-foreground">
                      {(summary.avg_response_time ?? 0).toFixed(2)}s
                    </div>
                    {summary.min_response_time !== undefined && summary.max_response_time !== undefined && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        {summary.min_response_time.toFixed(1)}s – {summary.max_response_time.toFixed(1)}s
                      </div>
                    )}
                  </div>

                  <div className="p-4 bg-background border border-border rounded-lg">
                    <div className="text-sm text-muted-foreground mb-1">Total Tokens</div>
                    <div className="text-2xl font-bold text-foreground">
                      {(summary.total_tokens ?? 0).toLocaleString()}
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {(summary.prompt_tokens ?? 0).toLocaleString()} prompt ·{' '}
                      {(summary.completion_tokens ?? 0).toLocaleString()} completion
                    </div>
                  </div>
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Timeline chart — only in per-agent mode */}
                  <div className="p-4 bg-background border border-border rounded-lg">
                    <h3 className="text-sm font-semibold text-foreground mb-4">Runs Over Time</h3>
                    {selectedAgentId ? (
                      timelineLoading ? (
                        <div className="flex items-center justify-center h-[220px]">
                          <Loader2 className="w-6 h-6 text-primary animate-spin" />
                        </div>
                      ) : (
                        <RunsLineChart data={timeline} />
                      )
                    ) : (
                      <div className="flex flex-col items-center justify-center h-[220px] text-muted-foreground gap-2">
                        <TrendingUp className="w-8 h-8" />
                        <span className="text-sm text-center">Select an agent to see the run timeline</span>
                      </div>
                    )}
                  </div>

                  {/* Tool usage chart */}
                  <div className="p-4 bg-background border border-border rounded-lg">
                    <h3 className="text-sm font-semibold text-foreground mb-4">Tool Usage</h3>
                    <ToolUsageBarChart data={toolUsage} />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
