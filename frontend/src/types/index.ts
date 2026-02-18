export interface User {
  id: string
  email: string
  full_name?: string
  is_verified: boolean
  is_active: boolean
  avatar_url?: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  owner_id: string
  created_at: string
  updated_at: string
}

export enum ItemType {
  EPIC = 'epic',
  STORY = 'story',
  BUG = 'bug',
  TASK = 'task',
  SPIKE = 'spike',
}

export enum ItemStatus {
  BACKLOG = 'backlog',
  IN_PROGRESS = 'in_progress',
  REVIEW = 'review',
  DONE = 'done',
}

export enum ItemPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface Item {
  id: string
  project_id: string
  type: ItemType
  title: string
  description?: string
  acceptance_criteria?: string
  status: ItemStatus
  priority: ItemPriority
  assignee_id?: string
  assigned_agent_id?: string
  parent_id?: string
  tags: string[]
  position: number
  created_at: string
  updated_at: string
  created_by?: string
}

export interface CreateItemData {
  project_id: string
  title: string
  description?: string
  acceptance_criteria?: string
  type?: ItemType
  priority?: ItemPriority
  assignee_id?: string
  parent_id?: string
  tags?: string[]
  status?: ItemStatus
}

export interface UpdateItemData {
  title?: string
  description?: string
  acceptance_criteria?: string
  type?: ItemType
  status?: ItemStatus
  priority?: ItemPriority
  assignee_id?: string
  parent_id?: string
  tags?: string[]
  position?: number
}
