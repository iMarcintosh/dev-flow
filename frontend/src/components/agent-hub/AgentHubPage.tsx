import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Loader2, Search } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { customAgentService } from '@/services/custom-agents'
import type { CustomAgent } from '@/types/custom-agent'
import { AgentCard } from './AgentCard'
import { AgentModal } from './AgentModal'
import { AgentDetailsModal } from './AgentDetailsModal'
import { TemplateGrid } from './TemplateGrid'

type TabType = 'my-agents' | 'templates' | 'marketplace'

export default function AgentHubPage() {
  const [activeTab, setActiveTab] = useState<TabType>('my-agents')
  const [searchQuery, setSearchQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAgent, setEditingAgent] = useState<CustomAgent | null>(null)
  const [selectedAgentForDetails, setSelectedAgentForDetails] = useState<CustomAgent | null>(null)
  const queryClient = useQueryClient()

  // Fetch my agents
  const { data: myAgents = [], isLoading: myAgentsLoading } = useQuery({
    queryKey: ['custom-agents'],
    queryFn: () => customAgentService.listAgents(true),
  })

  // Fetch marketplace agents
  const { data: marketplaceAgents = [], isLoading: marketplaceLoading } = useQuery({
    queryKey: ['marketplace-agents', searchQuery],
    queryFn: () => customAgentService.searchMarketplace(searchQuery || undefined),
    enabled: activeTab === 'marketplace',
  })

  const filteredAgents = searchQuery
    ? myAgents.filter(
        (agent) =>
          agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          agent.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : myAgents

  const handleCreateAgent = () => {
    setEditingAgent(null)
    setIsModalOpen(true)
  }

  const handleEditAgent = (agent: CustomAgent) => {
    setEditingAgent(agent)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingAgent(null)
  }

  const handleSaveAgent = () => {
    queryClient.invalidateQueries({ queryKey: ['custom-agents'] })
    handleCloseModal()
  }

  const isLoading =
    (activeTab === 'my-agents' && myAgentsLoading) ||
    (activeTab === 'marketplace' && marketplaceLoading)

  return (
    <AppLayout>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground">Agent Hub</h1>
                <p className="text-muted-foreground mt-2">
                  Create, manage and discover AI agents
                </p>
              </div>
              <button
                onClick={handleCreateAgent}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create Agent
              </button>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-6 mt-6 border-b border-border">
              <button
                onClick={() => setActiveTab('my-agents')}
                className={`pb-3 px-1 border-b-2 transition-colors ${
                  activeTab === 'my-agents'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                My Agents
              </button>
              <button
                onClick={() => setActiveTab('templates')}
                className={`pb-3 px-1 border-b-2 transition-colors ${
                  activeTab === 'templates'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Templates
              </button>
              <button
                onClick={() => setActiveTab('marketplace')}
                className={`pb-3 px-1 border-b-2 transition-colors ${
                  activeTab === 'marketplace'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                Marketplace
              </button>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        {activeTab !== 'templates' && (
          <div className="max-w-7xl mx-auto px-8 py-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search agents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          </div>
        )}

        {/* Content */}
        <div className="max-w-7xl mx-auto px-8 py-6">
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
          )}

          {!isLoading && activeTab === 'my-agents' && (
            <>
              {filteredAgents.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredAgents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      onEdit={() => handleEditAgent(agent)}
                      onDeleted={() =>
                        queryClient.invalidateQueries({ queryKey: ['custom-agents'] })
                      }
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    {searchQuery
                      ? 'No agents found matching your search'
                      : 'No agents yet. Create your first agent to get started!'}
                  </p>
                </div>
              )}
            </>
          )}

          {!isLoading && activeTab === 'templates' && (
            <TemplateGrid
              onTemplateUsed={() => {
                queryClient.invalidateQueries({ queryKey: ['custom-agents'] })
                setActiveTab('my-agents')
              }}
            />
          )}

          {!isLoading && activeTab === 'marketplace' && (
            <>
              {marketplaceAgents.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {marketplaceAgents.map((agent) => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      isMarketplace
                      onInstalled={() =>
                        queryClient.invalidateQueries({ queryKey: ['custom-agents'] })
                      }
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    {searchQuery ? 'No agents found' : 'No public agents available yet'}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {isModalOpen && (
        <AgentModal agent={editingAgent} onClose={handleCloseModal} onSave={handleSaveAgent} />
      )}
    </AppLayout>
  )
}


