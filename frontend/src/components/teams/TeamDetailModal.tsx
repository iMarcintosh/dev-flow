import { useState } from 'react'
import { useTeam, useAddTeamMember, useRemoveTeamMember, useUpdateMemberRole } from '@/services/queries'
import { X, Loader2, Users, Mail, Crown, Shield, User as UserIcon, Trash2 } from 'lucide-react'
import type { Team } from '@/services/teams'

interface TeamDetailModalProps {
  team: Team
  onClose: () => void
}

export default function TeamDetailModal({ team, onClose }: TeamDetailModalProps) {
  const [email, setEmail] = useState('')
  const [selectedRole, setSelectedRole] = useState<'member' | 'admin'>('member')
  
  const { data: teamDetail, isLoading } = useTeam(team.id)
  const addMemberMutation = useAddTeamMember(team.id)
  const removeMemberMutation = useRemoveTeamMember(team.id)
  const updateRoleMutation = useUpdateMemberRole(team.id)

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email.trim()) {
      alert('Please enter an email address')
      return
    }

    try {
      await addMemberMutation.mutateAsync({
        email: email.trim(),
        role: selectedRole,
      })
      setEmail('')
      setSelectedRole('member')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add member. Please try again.')
    }
  }

  const handleRemoveMember = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this member?')) {
      return
    }

    try {
      await removeMemberMutation.mutateAsync(userId)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to remove member.')
    }
  }

  const handleUpdateRole = async (userId: string, newRole: 'member' | 'admin') => {
    try {
      await updateRoleMutation.mutateAsync({ userId, role: newRole })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update role.')
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-500" />
      case 'admin':
        return <Shield className="w-4 h-4 text-blue-500" />
      default:
        return <UserIcon className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-yellow-500/10 text-yellow-500'
      case 'admin':
        return 'bg-blue-500/10 text-blue-500'
      default:
        return 'bg-muted text-muted-foreground'
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-foreground">{team.name}</h2>
              {team.description && (
                <p className="text-sm text-muted-foreground">{team.description}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Add Member Form */}
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-4">Add Member</h3>
            <form onSubmit={handleAddMember} className="space-y-3">
              <div className="flex gap-3">
                <div className="flex-1">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="member@example.com"
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value as 'member' | 'admin')}
                  className="px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  type="submit"
                  disabled={addMemberMutation.isPending || !email.trim()}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {addMemberMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Mail className="w-4 h-4" />
                  )}
                  Add
                </button>
              </div>
            </form>
          </div>

          {/* Members List */}
          <div>
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Members ({teamDetail?.members.length || 0})
            </h3>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-primary animate-spin" />
              </div>
            ) : (
              <div className="space-y-2">
                {teamDetail?.members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-3 bg-background border border-border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getRoleIcon(member.role)}
                      <div>
                        <div className="text-sm font-medium text-foreground">
                          {member.user_email}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-xs px-2 py-0.5 rounded ${getRoleBadgeColor(member.role)}`}>
                            {member.role}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {member.role !== 'owner' && (
                        <>
                          <select
                            value={member.role}
                            onChange={(e) => handleUpdateRole(member.user_id, e.target.value as 'member' | 'admin')}
                            className="text-sm px-2 py-1 bg-background border border-border rounded text-foreground"
                            disabled={updateRoleMutation.isPending}
                          >
                            <option value="member">Member</option>
                            <option value="admin">Admin</option>
                          </select>
                          <button
                            onClick={() => handleRemoveMember(member.user_id)}
                            disabled={removeMemberMutation.isPending}
                            className="p-2 hover:bg-destructive/10 rounded transition-colors"
                            title="Remove member"
                          >
                            <Trash2 className="w-4 h-4 text-destructive" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-muted text-foreground rounded-lg hover:bg-muted/80 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
