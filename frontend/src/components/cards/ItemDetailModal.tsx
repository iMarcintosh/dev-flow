import { useState } from 'react'
import { Item, ItemType, ItemPriority } from '@/types'
import { useUpdateItem, useDeleteItem } from '@/services/queries'
import { X, Trash2, Save } from 'lucide-react'
import { Select } from '@/components/ui/Select'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'

interface ItemDetailModalProps {
  item: Item
  onClose: () => void
}

export default function ItemDetailModal({ item, onClose }: ItemDetailModalProps) {
  const [title, setTitle] = useState(item.title)
  const [description, setDescription] = useState(item.description || '')
  const [acceptanceCriteria, setAcceptanceCriteria] = useState(item.acceptance_criteria || '')
  const [priority, setPriority] = useState(item.priority)
  const [type, setType] = useState(item.type)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const updateItem = useUpdateItem()
  const deleteItem = useDeleteItem()

  const handleSave = () => {
    updateItem.mutate(
      {
        id: item.id,
        data: {
          title,
          description,
          acceptance_criteria: acceptanceCriteria,
          priority,
          type,
        },
      },
      {
        onSuccess: () => onClose(),
      }
    )
  }

  const handleDelete = () => {
    deleteItem.mutate(item.id, {
      onSuccess: () => {
        setShowDeleteConfirm(false)
        onClose()
      },
    })
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-bold text-foreground">Item Details</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground p-1 hover:bg-muted rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground"
            />
          </div>

          {/* Type & Priority */}
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Type"
              value={type}
              onChange={(val) => setType(val as ItemType)}
              options={[
                { value: 'task', label: 'Task' },
                { value: 'bug', label: 'Bug' },
                { value: 'story', label: 'Story' },
                { value: 'epic', label: 'Epic' },
                { value: 'spike', label: 'Spike' },
              ]}
            />

            <Select
              label="Priority"
              value={priority}
              onChange={(val) => setPriority(val as ItemPriority)}
              options={[
                { value: 'low', label: 'Low' },
                { value: 'medium', label: 'Medium' },
                { value: 'high', label: 'High' },
                { value: 'critical', label: 'Critical' },
              ]}
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground resize-none"
              placeholder="Add a description..."
            />
          </div>

          {/* Acceptance Criteria */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Acceptance Criteria
            </label>
            <textarea
              value={acceptanceCriteria}
              onChange={(e) => setAcceptanceCriteria(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-foreground resize-none"
              placeholder="Define acceptance criteria..."
            />
          </div>

          {/* Metadata */}
          <div className="pt-4 border-t border-border space-y-2 text-sm text-muted-foreground">
            <div>
              <span className="font-medium">ID:</span> {item.id}
            </div>
            <div>
              <span className="font-medium">Status:</span> {item.status.replace('_', ' ')}
            </div>
            <div>
              <span className="font-medium">Created:</span>{' '}
              {new Date(item.created_at).toLocaleString()}
            </div>
            <div>
              <span className="font-medium">Updated:</span>{' '}
              {new Date(item.updated_at).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <button
            onClick={() => setShowDeleteConfirm(true)}
            disabled={deleteItem.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={updateItem.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {updateItem.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Item"
        message={`Are you sure you want to delete "${item.title}"?\n\nThis action cannot be undone.`}
        confirmText="Delete Item"
        confirmVariant="danger"
        isLoading={deleteItem.isPending}
      />
    </div>
  )
}
