import { useState } from 'react'
import { useProjectItems, useProjects, useCreateProject } from '@/services/queries'
import KanbanBoard from './KanbanBoard'
import ItemDetailModal from '@/components/cards/ItemDetailModal'
import AgentInputModal from '@/components/agent-hub/AgentInputModal'
import ChatWidget from '@/components/chatbot/ChatWidget'
import { AppLayout } from '@/components/layout/AppLayout'
import { Item } from '@/types'
import { Loader2, Sparkles, FolderPlus } from 'lucide-react'

export default function BoardPage() {
  const [selectedItem, setSelectedItem] = useState<Item | null>(null)
  const [showAgentModal, setShowAgentModal] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const { data: projects, isLoading: projectsLoading } = useProjects()
  const createProject = useCreateProject()
  const currentProject = projects?.[0] // For now, use first project
  
  const { data: items, isLoading: itemsLoading } = useProjectItems(currentProject?.id)

  if (projectsLoading || itemsLoading) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </AppLayout>
    )
  }

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectName.trim()) return
    await createProject.mutateAsync({ name: projectName.trim(), description: projectDescription.trim() || undefined })
    setShowCreateModal(false)
    setProjectName('')
    setProjectDescription('')
  }

  if (!currentProject) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background p-8 flex items-center justify-center">
          <div className="max-w-md w-full">
            {!showCreateModal ? (
              <div className="bg-card border border-border rounded-lg p-8 text-center">
                <FolderPlus className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-foreground mb-2">No Projects</h2>
                <p className="text-muted-foreground mb-6">Create your first project to get started.</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors mx-auto"
                >
                  <FolderPlus className="w-4 h-4" />
                  Projekt erstellen
                </button>
              </div>
            ) : (
              <div className="bg-card border border-border rounded-lg p-8">
                <h2 className="text-xl font-bold text-foreground mb-6">Neues Projekt erstellen</h2>
                <form onSubmit={handleCreateProject} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Name <span className="text-destructive">*</span>
                    </label>
                    <input
                      type="text"
                      value={projectName}
                      onChange={e => setProjectName(e.target.value)}
                      placeholder="Projektname"
                      required
                      autoFocus
                      className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Beschreibung <span className="text-muted-foreground text-xs">(optional)</span>
                    </label>
                    <textarea
                      value={projectDescription}
                      onChange={e => setProjectDescription(e.target.value)}
                      placeholder="Kurze Beschreibung des Projekts"
                      rows={3}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                    />
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button
                      type="submit"
                      disabled={!projectName.trim() || createProject.isPending}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {createProject.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FolderPlus className="w-4 h-4" />}
                      Erstellen
                    </button>
                    <button
                      type="button"
                      onClick={() => { setShowCreateModal(false); setProjectName(''); setProjectDescription('') }}
                      className="px-4 py-2 border border-border rounded-lg text-foreground hover:bg-muted transition-colors"
                    >
                      Abbrechen
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{currentProject.name}</h1>
            {currentProject.description && (
              <p className="text-muted-foreground mt-1">{currentProject.description}</p>
            )}
          </div>
          <button
            onClick={() => setShowAgentModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            AI Task Creator
          </button>
        </div>
      </div>

      {/* Board */}
      <div className="max-w-7xl mx-auto p-8 h-[calc(100vh-8rem)]">
        <KanbanBoard 
          items={items || []} 
          projectId={currentProject.id}
          onItemClick={setSelectedItem} 
        />
      </div>

      {/* Item Detail Modal */}
      {selectedItem && (
        <ItemDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
      )}

      {/* Agent Input Modal */}
      {showAgentModal && currentProject && (
        <AgentInputModal projectId={currentProject.id} onClose={() => setShowAgentModal(false)} />
      )}

      {/* Chat Widget */}
      {currentProject && <ChatWidget projectId={currentProject.id} />}
      </div>
    </AppLayout>
  )
}
