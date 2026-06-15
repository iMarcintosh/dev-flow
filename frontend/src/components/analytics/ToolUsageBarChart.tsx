import { Wrench } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { ToolUsageStat } from '@/services/analytics'

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_weather: 'Weather',
  execute_code: 'Code Exec',
  search_knowledge_base: 'Knowledge Base',
  read_url: 'Web Search',
  web_search: 'Web Search',
  create_task: 'Create Task',
  update_status: 'Update Status',
  add_comment: 'Add Comment',
}

const getToolDisplayName = (name: string) =>
  TOOL_DISPLAY_NAMES[name] ?? name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

const tooltipStyle = {
  contentStyle: { background: '#111111', border: '1px solid #262626', borderRadius: 8 },
  labelStyle: { color: '#ededed' },
  itemStyle: { color: '#a1a1aa' },
}

interface ToolUsageBarChartProps {
  data: ToolUsageStat[]
}

export function ToolUsageBarChart({ data }: ToolUsageBarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[220px] text-muted-foreground gap-2">
        <Wrench className="w-8 h-8" />
        <span className="text-sm">No tool usage data</span>
      </div>
    )
  }

  const chartData = [...data]
    .sort((a, b) => b.usage_count - a.usage_count)
    .slice(0, 8)
    .map((d) => ({ ...d, name: getToolDisplayName(d.tool_name) }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
        <XAxis dataKey="name" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
        <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} allowDecimals={false} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="usage_count" name="Uses" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
