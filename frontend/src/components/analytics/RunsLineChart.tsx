import { BarChart3 } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'
import type { TimelineData } from '@/services/analytics'

interface RunsLineChartProps {
  data: TimelineData[]
}

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

const tooltipStyle = {
  contentStyle: { background: '#111111', border: '1px solid #262626', borderRadius: 8 },
  labelStyle: { color: '#ededed' },
  itemStyle: { color: '#a1a1aa' },
}

export function RunsLineChart({ data }: RunsLineChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[220px] text-muted-foreground gap-2">
        <BarChart3 className="w-8 h-8" />
        <span className="text-sm">No timeline data</span>
      </div>
    )
  }

  const chartData = data.map((d) => ({ ...d, date: formatDate(d.date) }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
        <XAxis dataKey="date" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
        <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} allowDecimals={false} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#a1a1aa' }} />
        <Line
          type="monotone"
          dataKey="total_runs"
          name="Total Runs"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="failed_runs"
          name="Failed Runs"
          stroke="#ef4444"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
