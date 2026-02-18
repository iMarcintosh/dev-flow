import { Item, ItemType, ItemPriority, ItemStatus } from '@/types'
import { Bug, CheckCircle2, Circle, GitBranch, Lightbulb, Zap } from 'lucide-react'

interface ItemCardProps {
  item: Item
  onClick: () => void
}

const typeIcons = {
  epic: GitBranch,
  story: Circle,
  bug: Bug,
  task: CheckCircle2,
  spike: Lightbulb,
}

const typeColors = {
  epic: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  story: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  bug: 'text-red-400 bg-red-500/10 border-red-500/20',
  task: 'text-green-400 bg-green-500/10 border-green-500/20',
  spike: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
}

const priorityColors = {
  low: 'bg-gray-500',
  medium: 'bg-blue-500',
  high: 'bg-orange-500',
  critical: 'bg-red-500',
}

export default function ItemCard({ item, onClick }: ItemCardProps) {
  const Icon = typeIcons[item.type]
  const typeColor = typeColors[item.type]
  const priorityColor = priorityColors[item.priority]

  return (
    <div
      onClick={onClick}
      className="bg-card border border-border rounded-lg p-4 cursor-pointer hover:bg-card-hover hover:border-primary/30 transition-all group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className={`flex items-center gap-2 px-2 py-1 rounded border ${typeColor} text-xs font-medium`}>
          <Icon className="w-3 h-3" />
          <span className="capitalize">{item.type}</span>
        </div>
        <div className={`w-2 h-2 rounded-full ${priorityColor}`} title={item.priority} />
      </div>

      {/* Title */}
      <h3 className="text-foreground font-medium mb-2 line-clamp-2 group-hover:text-primary transition-colors">
        {item.title}
      </h3>

      {/* Description */}
      {item.description && (
        <p className="text-muted-foreground text-sm line-clamp-2 mb-3">
          {item.description}
        </p>
      )}

      {/* Tags */}
      {item.tags && item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {item.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-muted text-muted-foreground text-xs rounded"
            >
              {tag}
            </span>
          ))}
          {item.tags.length > 3 && (
            <span className="px-2 py-0.5 text-muted-foreground text-xs">
              +{item.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>#{item.id.slice(0, 8)}</span>
        {item.assignee_id && (
          <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-primary font-medium">A</span>
          </div>
        )}
      </div>
    </div>
  )
}
