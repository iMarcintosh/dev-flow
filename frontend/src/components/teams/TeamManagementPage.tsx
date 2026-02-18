import { useState } from 'react'
import { useTeams, useCreateTeam, useDeleteTeam } from '@/services/queries'
import { AppLayout } from '@/components/layout/AppLayout'
import { Plus, Users, Loader2, Trash2 } from 'lucide-react'
import CreateTeamModal from './CreateTeamModal'
import TeamDetailModal from './TeamDetailModal'
import type { Team } from '@/services/teams'

export default function TeamManagementPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null)
  
  const { data: teams, isLoading } = useTeams()
  const deleteTeamMutation = useDeleteTeam()

  const handleDeleteTeam = async (teamId: string) => {
    if (!confirm('Are you sure you want to delete this team? This cannot be undone.')) {
      return
    }
    
    try {
      await deleteTeamMutation.mutateAsync(teamId)
    } catch (error) {
      alert('Failed to delete team. You must be the owner to delete a team.')
    }
  }

  if (isLoading) {
    return (
      <AppLayout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="min-h-screen bg-background">
        {/* Header */}
        <div className="border-b border-border bg-card">
          <div className="max-w-7xl mx-auto px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground">Teams</h1>
                <p className="text-muted-foreground mt-1">
                  Manage your teams and collaborate with members
                </p>
              </div>
              <button
                onClick={() => setShowCreateModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Create Team
              </button>
            </div>
          </div>
        </div>

        {/* Teams Grid */}
        <div className="max-w-7xl mx-auto px-8 py-8">
          {!teams || teams.length === 0 ? (
            <div className="bg-card border border-border rounded-lg p-12 text-center">
              <Users className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-foreground mb-2">No Teams Yet</h2>
              <p className="text-muted-foreground mb-6">
                Create your first team to collaborate with others
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Create Team
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {teams.map((team) => (
                <div
                  key={team.id}
                  className="bg-card border border-border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => setSelectedTeam(team)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                        <Users className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-foreground">
                          {team.name}
                        </h3>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteTeam(team.id)
                      }}
                      className="opacity-0 group-hover:opacity-100 p-2 hover:bg-destructive/10 rounded transition-all"
                      title="Delete team"
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </button>
                  </div>
                  
                  {team.description && (
                    <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
                      {team.description}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>{team.member_count || 0} members</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span>🤖</span>
                      <span>{team.agent_count || 0} agents</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modals */}
        {showCreateModal && (
          <CreateTeamModal onClose={() => setShowCreateModal(false)} />
        )}
        
        {selectedTeam && (
          <TeamDetailModal
            team={selectedTeam}
            onClose={() => setSelectedTeam(null)}
          />
        )}
      </div>
    </AppLayout>
  )
}
