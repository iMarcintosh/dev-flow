import api from './api'

export interface Team {
  id: string
  name: string
  description?: string
  created_by: string
  created_at: string
  updated_at: string
  member_count?: number
  agent_count?: number
}

export interface TeamMember {
  id: string
  team_id: string
  user_id: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
  user_email?: string
  user_name?: string
}

export interface TeamDetail extends Team {
  members: TeamMember[]
}

export interface CreateTeamRequest {
  name: string
  description?: string
}

export interface AddMemberRequest {
  email: string
  role?: 'member' | 'admin'
}

export interface UpdateRoleRequest {
  role: 'member' | 'admin'
}

// List user's teams
export const listTeams = async (): Promise<Team[]> => {
  const response = await api.get('/teams')
  return response.data
}

// Create a team
export const createTeam = async (data: CreateTeamRequest): Promise<Team> => {
  const response = await api.post('/teams', data)
  return response.data
}

// Get team details
export const getTeam = async (teamId: string): Promise<TeamDetail> => {
  const response = await api.get(`/teams/${teamId}`)
  return response.data
}

// Delete team (owner only)
export const deleteTeam = async (teamId: string): Promise<void> => {
  await api.delete(`/teams/${teamId}`)
}

// List team members
export const listTeamMembers = async (teamId: string): Promise<TeamMember[]> => {
  const response = await api.get(`/teams/${teamId}/members`)
  return response.data
}

// Add team member
export const addTeamMember = async (
  teamId: string,
  data: AddMemberRequest
): Promise<TeamMember> => {
  const response = await api.post(`/teams/${teamId}/members`, data)
  return response.data
}

// Update member role
export const updateMemberRole = async (
  teamId: string,
  userId: string,
  data: UpdateRoleRequest
): Promise<TeamMember> => {
  const response = await api.patch(`/teams/${teamId}/members/${userId}`, data)
  return response.data
}

// Remove team member
export const removeMemberTeam = async (
  teamId: string,
  userId: string
): Promise<void> => {
  await api.delete(`/teams/${teamId}/members/${userId}`)
}

// List team agents
export const listTeamAgents = async (teamId: string): Promise<any[]> => {
  const response = await api.get(`/teams/${teamId}/agents`)
  return response.data
}
