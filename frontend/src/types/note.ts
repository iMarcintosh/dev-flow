export interface Note {
  id: string
  user_id: string
  project_id?: string | null
  title: string
  content: string
  tags: string[]
  is_pinned: boolean
  chroma_indexed: boolean
  created_at: string
  updated_at: string
}

export interface NoteCreate {
  title?: string
  content?: string
  tags?: string[]
  is_pinned?: boolean
  project_id?: string
}

export interface NoteUpdate {
  title?: string
  content?: string
  tags?: string[]
  is_pinned?: boolean
  project_id?: string | null
}

export interface NoteListResponse {
  notes: Note[]
  total: number
}

export type BlockType = 'h1' | 'h2' | 'h3' | 'code' | 'bullet' | 'numbered' | 'quote' | 'divider'

export interface SlashCommand {
  command: string
  label: string
  description: string
  prefix: string
  blockType: BlockType
}
