import { apiClient } from './client';
import type { ApiResponse } from '../types/common';
import type { ScoringSettings, UpdateScoringSettingsRequest } from '../types/scoring';

export const scoringApi = {
  getSettings: async (): Promise<ApiResponse<ScoringSettings>> => {
    return apiClient.get<ScoringSettings>('/api/v1/scoring/settings');
  },

  updateSettings: async (data: UpdateScoringSettingsRequest): Promise<ApiResponse<ScoringSettings>> => {
    return apiClient.put<ScoringSettings>('/api/v1/scoring/settings', data);
  },
};
