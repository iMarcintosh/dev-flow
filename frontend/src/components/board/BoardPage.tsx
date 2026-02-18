import { useState } from 'react'
import { useProjectItems, useProjects } from '@/services/queries'
import KanbanBoard from './KanbanBoard'
import ItemDetailModal from '@/components/cards/ItemDetailModal'
import AgentInputModal from '@/components/agent-hub/AgentInputModal'
import ChatWidget from '@/components/chatbot/ChatWidget'
import { AppLayout } from '@/components/layout/AppLayout'
import { Item } from '@/types'
import { Loader2, Sparkles } from 'lucide-react'

export default function BoardPage() {
  const [selectedItem, setSelectedItem] = useState<Item | null>(null)
  const [showAgentModal, setShowAgentModal] = useState(false)
  const { data: projects, isLoading: projectsLoading } = useProjects()
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

  if (!currentProject) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background p-8">
          <div className="max-w-7xl mx-auto">
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <h2 className="text-2xl font-bold text-foreground mb-4">No Projects</h2>
              <p className="text-muted-foreground">Create your first project to get started.</p>
            </div>
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
        <KanbanBoard items={items || []} onItemClick={setSelectedItem} />
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
