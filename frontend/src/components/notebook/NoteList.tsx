import { useState } from 'react'
import { Search, Plus, Pin } from 'lucide-react'
import { useNotes, useNoteTags, useCreateNote } from '@/services/noteQueries'
import type { Note } from '@/types/note'

interface NoteListProps {
  selectedNoteId: string | undefined
  onSelectNote: (note: Note) => void
  onNoteCreated: (note: Note) => void
  projectId?: string
}

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6} /g, '')
    .replace(/\*\*|__|\*|_/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]+`/g, '')
    .replace(/> /g, '')
    .replace(/- |^\d+\. /gm, '')
    .replace(/---/g, '')
    .trim()
}

export function NoteList({ selectedNoteId, onSelectNote, onNoteCreated, projectId }: NoteListProps) {
  const [search, setSearch] = useState('')
  const [activeTag, setActiveTag] = useState<string | undefined>(undefined)

  const { data: tagsData = [] } = useNoteTags()
  const { data: notesData, isLoading } = useNotes({
    search: search || undefined,
    tag: activeTag,
    project_id: projectId,
  })
  const createNote = useCreateNote()

  const notes = notesData?.notes ?? []
  const pinnedNotes = notes.filter((n) => n.is_pinned)
  const unpinnedNotes = notes.filter((n) => !n.is_pinned)

  const handleCreateNote = async () => {
    const note = await createNote.mutateAsync({
      title: 'Untitled',
      content: '',
      tags: [],
      project_id: projectId,
    })
    onNoteCreated(note)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 pt-3 pb-2 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-foreground">Notes</h2>
          <button
            onClick={handleCreateNote}
            disabled={createNote.isPending}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Plus className="w-3 h-3" />
            New
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-2">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search notes..."
            className="w-full pl-8 pr-3 py-1.5 bg-background border border-border rounded-md text-xs text-foreground placeholder:text-muted-foreground outline-none focus:ring-1 focus:ring-primary"
          />
        </div>

        {/* Tag Filter Pills */}
        {tagsData.length > 0 && (
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setActiveTag(undefined)}
              className={`px-2 py-0.5 rounded-full text-xs transition-colors ${
                !activeTag
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`}
            >
              All
            </button>
            {tagsData.map((tag) => (
              <button
                key={tag}
                onClick={() => setActiveTag(activeTag === tag ? undefined : tag)}
                className={`px-2 py-0.5 rounded-full text-xs transition-colors ${
                  activeTag === tag
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Notes list */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        {isLoading ? (
          <div className="flex items-center justify-center h-20 text-xs text-muted-foreground">
            Loading...
          </div>
        ) : notes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 gap-2">
            <p className="text-xs text-muted-foreground">No notes yet</p>
            <button
              onClick={handleCreateNote}
              className="text-xs text-primary hover:underline"
            >
              Create your first note
            </button>
          </div>
        ) : (
          <>
            {/* Pinned section */}
            {pinnedNotes.length > 0 && (
              <div className="mb-3">
                <div className="flex items-center gap-1 px-1 mb-1">
                  <Pin className="w-3 h-3 text-amber-400" />
                  <span className="text-xs text-muted-foreground font-medium">Pinned</span>
                </div>
                {pinnedNotes.map((note) => (
                  <NoteCard
                    key={note.id}
                    note={note}
                    isSelected={note.id === selectedNoteId}
                    onSelect={onSelectNote}
                    formatDate={formatDate}
                  />
                ))}
                {unpinnedNotes.length > 0 && (
                  <div className="border-t border-border mt-2 mb-2" />
                )}
              </div>
            )}

            {/* All notes */}
            {unpinnedNotes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                isSelected={note.id === selectedNoteId}
                onSelect={onSelectNote}
                formatDate={formatDate}
              />
            ))}
          </>
        )}
      </div>
    </div>
  )
}

function NoteCard({
  note,
  isSelected,
  onSelect,
  formatDate,
}: {
  note: Note
  isSelected: boolean
  onSelect: (note: Note) => void
  formatDate: (d: string) => string
}) {
  const preview = stripMarkdown(note.content).slice(0, 80)

  return (
    <button
      onClick={() => onSelect(note)}
      className={`w-full text-left px-3 py-2.5 rounded-lg mb-1 transition-colors ${
        isSelected
          ? 'bg-primary/10 border border-primary/20'
          : 'hover:bg-accent border border-transparent'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-0.5">
        <span className="text-sm font-medium text-foreground truncate flex-1">
          {note.title || 'Untitled'}
        </span>
        <span className="text-xs text-muted-foreground flex-shrink-0">
          {formatDate(note.updated_at)}
        </span>
      </div>
      {preview && (
        <p className="text-xs text-muted-foreground truncate mb-1">{preview}</p>
      )}
      {note.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {note.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-1.5 py-0 rounded-full bg-muted text-muted-foreground text-xs"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </button>
  )
}
