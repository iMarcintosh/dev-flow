/**
 * Knowledge Base API Service
 * 
 * Handles file uploads and search for agent knowledge bases.
 */
import api from './api';

export interface KnowledgeFile {
  file_id: string;
  filename: string;
  file_type: string;
}

export interface UploadResponse {
  success: boolean;
  file_id?: string;
  filename?: string;
  chunks_added?: number;
  error?: string;
}

export interface SearchResult {
  text: string;
  metadata: {
    filename: string;
    file_id: string;
    chunk_index: number;
    file_type: string;
  };
  distance?: number;
}

/**
 * Upload file to agent's knowledge base
 */
export const uploadFile = async (agentId: string, file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post(`/api/knowledge-base/${agentId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

/**
 * List all files in agent's knowledge base
 */
export const listFiles = async (agentId: string): Promise<KnowledgeFile[]> => {
  const response = await api.get(`/api/knowledge-base/${agentId}/files`);
  return response.data;
};

/**
 * Delete file from knowledge base
 */
export const deleteFile = async (agentId: string, fileId: string): Promise<void> => {
  await api.delete(`/api/knowledge-base/${agentId}/files/${fileId}`);
};

/**
 * Search agent's knowledge base
 */
export const searchKnowledgeBase = async (
  agentId: string,
  query: string,
  nResults: number = 5
): Promise<SearchResult[]> => {
  const response = await api.post(`/api/knowledge-base/${agentId}/search`, {
    query,
    n_results: nResults,
  });
  return response.data;
};
