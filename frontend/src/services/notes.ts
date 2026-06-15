import api from '@/services/api'
import type { Note, NoteCreate, NoteUpdate, NoteListResponse } from '@/types/note'

export interface NoteListParams {
  tag?: string
  project_id?: string
  pinned_only?: boolean
  search?: string
  limit?: number
  offset?: number
}

export const notesService = {
  async list(params: NoteListParams = {}): Promise<NoteListResponse> {
    const searchParams = new URLSearchParams()
    if (params.tag) searchParams.set('tag', params.tag)
    if (params.project_id) searchParams.set('project_id', params.project_id)
    if (params.pinned_only) searchParams.set('pinned_only', 'true')
    if (params.search) searchParams.set('search', params.search)
    if (params.limit) searchParams.set('limit', String(params.limit))
    if (params.offset) searchParams.set('offset', String(params.offset))
    const query = searchParams.toString()
    const { data } = await api.get<NoteListResponse>(`/api/notes/${query ? '?' + query : ''}`)
    return data
  },

  async get(id: string): Promise<Note> {
    const { data } = await api.get<Note>(`/api/notes/${id}`)
    return data
  },

  async create(noteData: NoteCreate): Promise<Note> {
    const { data } = await api.post<Note>('/api/notes/', noteData)
    return data
  },

  async update(id: string, noteData: NoteUpdate): Promise<Note> {
    const { data } = await api.patch<Note>(`/api/notes/${id}`, noteData)
    return data
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/notes/${id}`)
  },

  async listTags(): Promise<string[]> {
    const { data } = await api.get<string[]>('/api/notes/tags/all')
    return data
  },
}
