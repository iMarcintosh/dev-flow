/**
 * API Service for Scheduled Agent Runs
 */

import api from './api';

export interface ScheduledRun {
  id: string;
  agent_id: string;
  status: 'success' | 'failed';
  input_text?: string;
  response?: string;
  error?: string;
  response_time?: number;
  tools_used?: number;
  executed_at: string;
}

export const scheduledRunsService = {
  /**
   * Get scheduled run history for an agent
   */
  async getScheduledRuns(agentId: string, limit: number = 20): Promise<ScheduledRun[]> {
    const response = await api.get(`/api/custom-agents/${agentId}/scheduled-runs`, {
      params: { limit },
    });
    return response.data;
  },
};
