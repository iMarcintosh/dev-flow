import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { Item, ItemStatus } from '@/types'
import SortableItemCard from './SortableItemCard'
import { Plus } from 'lucide-react'

interface KanbanColumnProps {
  id: ItemStatus
  title: string
  items: Item[]
  onItemClick: (item: Item) => void
}

const statusColors = {
  backlog: 'border-gray-500/20',
  in_progress: 'border-blue-500/20',
  review: 'border-orange-500/20',
  done: 'border-green-500/20',
}

export default function KanbanColumn({ id, title, items, onItemClick }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id })

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-foreground font-semibold">{title}</h2>
          <span className="text-muted-foreground text-sm bg-muted px-2 py-0.5 rounded">
            {items.length}
          </span>
        </div>
        <button className="text-muted-foreground hover:text-foreground p-1 hover:bg-muted rounded transition-colors">
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Items Container */}
      <div
        ref={setNodeRef}
        className={`flex-1 border-2 border-dashed rounded-lg p-3 transition-colors ${
          statusColors[id]
        } ${isOver ? 'border-primary bg-primary/5' : 'border-transparent'}`}
      >
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-3">
            {items.map((item) => (
              <SortableItemCard key={item.id} item={item} onItemClick={onItemClick} />
            ))}
          </div>
        </SortableContext>

        {items.length === 0 && (
          <div className="text-center py-12 text-muted-foreground text-sm">
            Drop items here
          </div>
        )}
      </div>
    </div>
  )
}
