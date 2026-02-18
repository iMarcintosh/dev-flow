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
