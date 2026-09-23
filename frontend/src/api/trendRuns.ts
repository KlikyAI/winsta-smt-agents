import { apiClient } from './client';
import type { ApiResponse, PaginatedResponse } from '../types/common';
import type { CreateTrendRunRequest, TrendRun } from '../types/trendRun';

export const trendRunsApi = {
  createRun: async (data: CreateTrendRunRequest): Promise<ApiResponse<{ id: string; status: string }>> => {
    return apiClient.post<{ id: string; status: string }>('/api/v1/trend-runs', data);
  },

  getRuns: async (page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<TrendRun>>> => {
    return apiClient.get<PaginatedResponse<TrendRun>>('/api/v1/trend-runs', { page, page_size: pageSize });
  },

  getRunById: async (runId: string): Promise<ApiResponse<TrendRun>> => {
    return apiClient.get<TrendRun>(`/api/v1/trend-runs/${runId}`);
  },

  cancelRun: async (runId: string): Promise<ApiResponse<TrendRun>> => {
    return apiClient.post<TrendRun>(`/api/v1/trend-runs/${runId}/cancel`);
  },
};
