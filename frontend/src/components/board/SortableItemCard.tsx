import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Item } from '@/types'
import ItemCard from '@/components/cards/ItemCard'

interface SortableItemCardProps {
  item: Item
  projectId: string
  onItemClick: (item: Item) => void
}

export default function SortableItemCard({ item, projectId, onItemClick }: SortableItemCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <ItemCard item={item} projectId={projectId} onClick={() => onItemClick(item)} />
    </div>
  )
}
