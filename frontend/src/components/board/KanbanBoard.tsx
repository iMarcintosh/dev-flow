import { useMemo, useState } from 'react'
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragEndEvent,
} from '@dnd-kit/core'
import { arrayMove, SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { Item, ItemStatus } from '@/types'
import KanbanColumn from './KanbanColumn'
import ItemCard from '@/components/cards/ItemCard'
import { useUpdateItemStatus } from '@/services/queries'

interface KanbanBoardProps {
  projectId: string
  items: Item[]
  onItemClick: (item: Item) => void
}

const COLUMNS: { id: ItemStatus; title: string }[] = [
  { id: 'backlog', title: 'Backlog' },
  { id: 'in_progress', title: 'In Progress' },
  { id: 'review', title: 'Review' },
  { id: 'done', title: 'Done' },
]

export default function KanbanBoard({ projectId, items, onItemClick }: KanbanBoardProps) {
  const [activeItem, setActiveItem] = useState<Item | null>(null)
  const updateStatus = useUpdateItemStatus()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor)
  )

  const itemsByStatus = useMemo(() => {
    const grouped: Record<ItemStatus, Item[]> = {
      backlog: [],
      in_progress: [],
      review: [],
      done: [],
    }

    items.forEach((item) => {
      if (grouped[item.status]) {
        grouped[item.status].push(item)
      }
    })

    // Sort by position
    Object.keys(grouped).forEach((status) => {
      grouped[status as ItemStatus].sort((a, b) => a.position - b.position)
    })

    return grouped
  }, [items])

  const handleDragStart = (event: DragStartEvent) => {
    const item = items.find((i) => i.id === event.active.id)
    setActiveItem(item || null)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    setActiveItem(null)

    if (!over) return

    const activeItem = items.find((i) => i.id === active.id)
    if (!activeItem) return

    // Check if dropped on a column
    const overColumn = COLUMNS.find((col) => col.id === over.id)
    if (overColumn && activeItem.status !== overColumn.id) {
      // Move to different column
      const targetItems = itemsByStatus[overColumn.id]
      const newPosition = targetItems.length > 0 ? targetItems[targetItems.length - 1].position + 1 : 1

      updateStatus.mutate({
        id: activeItem.id,
        status: overColumn.id,
        position: newPosition,
      })
    } else {
      // Reorder within same column (simplified - just using position)
      const overItem = items.find((i) => i.id === over.id)
      if (overItem && activeItem.status === overItem.status && activeItem.id !== overItem.id) {
        const columnItems = itemsByStatus[activeItem.status]
        const oldIndex = columnItems.findIndex((i) => i.id === activeItem.id)
        const newIndex = columnItems.findIndex((i) => i.id === overItem.id)

        const reordered = arrayMove(columnItems, oldIndex, newIndex)
        const newPosition = (reordered[newIndex - 1]?.position || 0 + reordered[newIndex + 1]?.position || 100) / 2

        updateStatus.mutate({
          id: activeItem.id,
          status: activeItem.status,
          position: newPosition,
        })
      }
    }
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-4 gap-6 h-full">
        {COLUMNS.map((column) => (
          <KanbanColumn
            key={column.id}
            id={column.id}
            title={column.title}
            items={itemsByStatus[column.id]}
            projectId={projectId}
            onItemClick={onItemClick}
          />
        ))}
      </div>

      <DragOverlay>
        {activeItem ? (
          <div className="rotate-3">
            <ItemCard item={activeItem} projectId={projectId} onClick={() => {}} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}
