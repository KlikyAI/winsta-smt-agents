import { apiClient } from './client';
import type { ApiResponse } from '../types/common';
import type { PromptPackage } from '../types/promptPackage';

export const promptPackagesApi = {
  getPackages: async (trendId: string): Promise<ApiResponse<PromptPackage[]>> => {
    return apiClient.get<PromptPackage[]>(`/api/v1/trends/${trendId}/prompt-packages`);
  },

  getLatest: async (trendId: string): Promise<ApiResponse<PromptPackage>> => {
    return apiClient.get<PromptPackage>(`/api/v1/trends/${trendId}/prompt-packages/latest`);
  },

  getIntegrationPrompt: async (trendId: string): Promise<ApiResponse<PromptPackage>> => {
    return apiClient.get<PromptPackage>(`/api/v1/trends/${trendId}/prompt`);
  },

  regenerate: async (trendId: string): Promise<ApiResponse<{ trend_id: string }>> => {
    return apiClient.post<{ trend_id: string }>(`/api/v1/trends/${trendId}/regenerate`);
  },
};
