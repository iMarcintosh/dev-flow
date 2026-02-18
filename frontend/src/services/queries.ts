import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'
import { Item, CreateItemData, UpdateItemData, Project, ItemStatus } from '@/types'
import type { ChatMessage, ChatResponse } from '@/types/chat'

export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const { data } = await api.get<Project[]>('/api/projects/')
      return data
    },
  })
}

export const useProjectItems = (projectId: string | undefined) => {
  return useQuery({
    queryKey: ['items', projectId],
    queryFn: async () => {
      if (!projectId) return []
      const { data } = await api.get<Item[]>(`/api/items/?project_id=${projectId}`)
      return data
    },
    enabled: !!projectId,
  })
}

export const useCreateItem = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (itemData: CreateItemData) => {
      const { data } = await api.post<Item>('/api/items/', itemData)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['items', data.project_id] })
    },
  })
}

export const useUpdateItem = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data: itemData }: { id: string; data: UpdateItemData }) => {
      const { data } = await api.patch<Item>(`/api/items/${id}`, itemData)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['items', data.project_id] })
    },
  })
}

export const useUpdateItemStatus = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, status, position }: { id: string; status: ItemStatus; position?: number }) => {
      const { data } = await api.patch<Item>(`/api/items/${id}/status`, { status, position })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['items', data.project_id] })
    },
  })
}

export const useDeleteItem = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/items/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

export const useCreateProject = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (projectData: { name: string; description?: string }) => {
      const { data } = await api.post<Project>('/api/projects/', projectData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}


// Agent Queries
export const useAgents = () => {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await api.get('/api/agents/')
      return data
    },
  })
}

export const useStartAgent = () => {
  return useMutation({
    mutationFn: async ({ agentName, projectId, text }: { agentName: string; projectId: string; text: string }) => {
      const { data } = await api.post(`/api/agents/${agentName}/run`, {
        project_id: projectId,
        data: { text },
      })
      return data
    },
  })
}

export const useAgentRun = (runId: string | undefined) => {
  return useQuery({
    queryKey: ['agentRun', runId],
    queryFn: async () => {
      if (!runId) return null
      const { data } = await api.get(`/api/agents/runs/${runId}`)
      return data
    },
    enabled: !!runId,
    refetchInterval: (data: any) => {
      // Poll while running
      if (data?.status === 'pending' || data?.status === 'running') {
        return 1000
      }
      return false
    },
  })
}

export const useApplyAgentResults = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (runId: string) => {
      const { data } = await api.post(`/api/agents/runs/${runId}/apply`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] })
    },
  })
}

// Chat queries
export const useChatHistory = (projectId: string | undefined) => {
  return useQuery({
    queryKey: ['chat', projectId],
    queryFn: async () => {
      if (!projectId) return []
      const { data } = await api.get<ChatMessage[]>(`/api/chat/history?project_id=${projectId}`)
      return data
    },
    enabled: !!projectId,
  })
}

export const useSendChatMessage = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ projectId, message }: { projectId: string; message: string }) => {
      const { data } = await api.post<ChatResponse>('/api/chat/', {
        project_id: projectId,
        message,
      })
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', variables.projectId] })
    },
  })
}

// Model selection queries
export const useAvailableModels = () => {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await api.get('/api/models')
      return response.data
    },
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}

export const useUpdateUserPreferences = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (preferences: Record<string, string>) => {
      const response = await api.patch('/api/auth/me/preferences', preferences)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })
}

export const useRefreshModels = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/api/models/refresh')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
    },
  })
}

// API Keys Management
export interface ApiKeyStatus {
  provider: string
  status: 'personal' | 'global' | 'none'
  masked_key: string | null
}

export interface ApiKeyStatusResponse {
  keys: ApiKeyStatus[]
}

export interface TestKeyRequest {
  provider: 'anthropic' | 'openai' | 'openrouter'
  api_key: string
}

export interface TestKeyResponse {
  valid: boolean
  error: string | null
}

export const useApiKeyStatus = () => {
  return useQuery({
    queryKey: ['api-keys', 'status'],
    queryFn: async () => {
      const { data } = await api.get<ApiKeyStatusResponse>('/api/api-keys/status')
      return data
    },
  })
}

export const useTestApiKey = () => {
  return useMutation({
    mutationFn: async (request: TestKeyRequest) => {
      const { data } = await api.post<TestKeyResponse>('/api/api-keys/test', request)
      return data
    },
  })
}

export const useUpdateApiKey = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ provider, api_key }: { provider: string; api_key: string }) => {
      const { data } = await api.put(`/api/api-keys/${provider}`, { api_key })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys', 'status'] })
    },
  })
}

export const useDeleteApiKey = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (provider: string) => {
      const { data } = await api.delete(`/api/api-keys/${provider}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys', 'status'] })
    },
  })
}

// ==================== TEAMS ====================

import * as teamsApi from './teams'
import type { Team, TeamDetail, CreateTeamRequest, AddMemberRequest, UpdateRoleRequest } from './teams'

export const useTeams = () => {
  return useQuery({
    queryKey: ['teams'],
    queryFn: teamsApi.listTeams,
  })
}

export const useTeam = (teamId: string | undefined) => {
  return useQuery({
    queryKey: ['teams', teamId],
    queryFn: () => teamsApi.getTeam(teamId!),
    enabled: !!teamId,
  })
}

export const useCreateTeam = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateTeamRequest) => teamsApi.createTeam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
    },
  })
}

export const useDeleteTeam = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (teamId: string) => teamsApi.deleteTeam(teamId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] })
    },
  })
}

export const useAddTeamMember = (teamId: string) => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: AddMemberRequest) => teamsApi.addTeamMember(teamId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] })
    },
  })
}

export const useRemoveTeamMember = (teamId: string) => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (userId: string) => teamsApi.removeMemberTeam(teamId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] })
    },
  })
}

export const useUpdateMemberRole = (teamId: string) => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: 'member' | 'admin' }) =>
      teamsApi.updateMemberRole(teamId, userId, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams', teamId] })
    },
  })
}
