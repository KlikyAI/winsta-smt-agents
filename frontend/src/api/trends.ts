import { apiClient } from './client';
import type { ApiResponse, PaginatedResponse } from '../types/common';
import type { TrendDetail, TrendListItem, TrendQueryParams } from '../types/trend';

export interface BatchReviewPayload {
  trend_ids: string[];
  decision: 'approve' | 'reject';
  notes?: string;
}

export interface BatchReviewResult {
  processed_count: number;
  processed_ids: string[];
  errors: any[];
  status: string;
}

export const trendsApi = {
  getTrends: async (params?: TrendQueryParams): Promise<ApiResponse<PaginatedResponse<TrendListItem>>> => {
    return apiClient.get<PaginatedResponse<TrendListItem>>('/api/v1/trends', params);
  },

  getTrendDetail: async (trendId: string): Promise<ApiResponse<TrendDetail>> => {
    return apiClient.get<TrendDetail>(`/api/v1/trends/${trendId}`);
  },

  batchReview: async (payload: BatchReviewPayload): Promise<ApiResponse<BatchReviewResult>> => {
    return apiClient.post<BatchReviewResult>('/api/v1/approvals/batch', payload);
  },
};
