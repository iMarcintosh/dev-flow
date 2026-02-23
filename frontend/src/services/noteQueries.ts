import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notesService, NoteListParams } from '@/services/notes'
import type { NoteCreate, NoteUpdate } from '@/types/note'

export const noteKeys = {
  all: ['notes'] as const,
  lists: () => [...noteKeys.all, 'list'] as const,
  list: (params: NoteListParams) => [...noteKeys.lists(), params] as const,
  details: () => [...noteKeys.all, 'detail'] as const,
  detail: (id: string) => [...noteKeys.details(), id] as const,
  tags: () => [...noteKeys.all, 'tags'] as const,
}

export function useNotes(params: NoteListParams = {}) {
  return useQuery({
    queryKey: noteKeys.list(params),
    queryFn: () => notesService.list(params),
  })
}

export function useNote(id: string | undefined) {
  return useQuery({
    queryKey: noteKeys.detail(id!),
    queryFn: () => notesService.get(id!),
    enabled: !!id,
  })
}

export function useNoteTags() {
  return useQuery({
    queryKey: noteKeys.tags(),
    queryFn: () => notesService.listTags(),
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: NoteCreate) => notesService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() })
      queryClient.invalidateQueries({ queryKey: noteKeys.tags() })
    },
  })
}

export function useUpdateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NoteUpdate }) =>
      notesService.update(id, data),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() })
      queryClient.invalidateQueries({ queryKey: noteKeys.detail(note.id) })
      queryClient.invalidateQueries({ queryKey: noteKeys.tags() })
    },
  })
}

export function useDeleteNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => notesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: noteKeys.lists() })
      queryClient.invalidateQueries({ queryKey: noteKeys.tags() })
    },
  })
}
