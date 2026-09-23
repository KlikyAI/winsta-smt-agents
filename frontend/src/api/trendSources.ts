import { apiClient } from './client';
import type { ApiResponse } from '../types/common';
import type { TrendSource, UpdateTrendSourceRequest } from '../types/trendSource';

export const trendSourcesApi = {
  getSources: async (): Promise<ApiResponse<TrendSource[]>> => {
    return apiClient.get<TrendSource[]>('/api/v1/trend-sources');
  },

  getSourceById: async (id: string): Promise<ApiResponse<TrendSource>> => {
    return apiClient.get<TrendSource>(`/api/v1/trend-sources/${id}`);
  },

  updateSource: async (id: string, data: UpdateTrendSourceRequest): Promise<ApiResponse<TrendSource>> => {
    return apiClient.patch<TrendSource>(`/api/v1/trend-sources/${id}`, data);
  },

  enableSource: async (id: string): Promise<ApiResponse<TrendSource>> => {
    return apiClient.post<TrendSource>(`/api/v1/trend-sources/${id}/enable`);
  },

  disableSource: async (id: string): Promise<ApiResponse<TrendSource>> => {
    return apiClient.post<TrendSource>(`/api/v1/trend-sources/${id}/disable`);
  },
};
