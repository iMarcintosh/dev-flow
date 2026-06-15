import { useState } from 'react'
import { BookOpen } from 'lucide-react'
import { useRouterState } from '@tanstack/react-router'
import { Sidebar } from '@/components/layout/Sidebar'
import { NoteList } from './NoteList'
import { NoteEditor } from './NoteEditor'
import type { Note } from '@/types/note'

export default function NotebookPage() {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)

  const routerState = useRouterState()
  const searchParams = routerState.location.search
  const urlParams = new URLSearchParams(searchParams)
  const activeProjectId = urlParams.get('project_id') ?? undefined

  const handleNoteCreated = (note: Note) => {
    setSelectedNote(note)
  }

  const handleNoteDeleted = () => {
    setSelectedNote(null)
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 overflow-hidden">
        {/* Note List sidebar */}
        <div className="w-72 flex-shrink-0 border-r border-border bg-card overflow-hidden flex flex-col">
          <NoteList
            selectedNoteId={selectedNote?.id}
            onSelectNote={setSelectedNote}
            onNoteCreated={handleNoteCreated}
            projectId={activeProjectId}
          />
        </div>

        {/* Editor area */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {selectedNote ? (
            <NoteEditor
              key={selectedNote.id}
              note={selectedNote}
              onDeleted={handleNoteDeleted}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
              <BookOpen className="w-12 h-12 opacity-20" />
              <p className="text-sm">Select a note or create a new one</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
