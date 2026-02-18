export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatResponse {
  message: string;
  referenced_items: Array<{
    id: string;
    title: string;
    type: string;
    status: string;
  }>;
}
