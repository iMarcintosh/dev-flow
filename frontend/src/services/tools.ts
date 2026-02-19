import { api } from './api'

export interface AvailableTool {
  id: string
  name: string
  description: string
  category: string
  functions: string[]
}

export const toolsService = {
  async getAvailableTools(): Promise<AvailableTool[]> {
    const response = await api.get('/api/tools/available')
    return response.data.tools
  },
}
