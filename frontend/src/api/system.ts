import { apiClient } from './client';

export interface HealthResponse {
  status: string;
  checks?: {
    database: string;
    redis: string;
  };
}

export const systemApi = {
  getHealth: async () => {
    return apiClient.get<HealthResponse>('/health');
  },

  getReadiness: async () => {
    return apiClient.get<HealthResponse>('/health/ready');
  },

  getSettings: async () => {
    return apiClient.get<any>('/api/v1/settings');
  },
};
