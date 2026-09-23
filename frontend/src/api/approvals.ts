import { apiClient } from './client';
import type { ApiResponse } from '../types/common';
import type { ReviewRequest, TrendReview } from '../types/review';

export const approvalsApi = {
  reviewTrend: async (trendId: string, data: ReviewRequest): Promise<ApiResponse<TrendReview>> => {
    return apiClient.post<TrendReview>(`/api/v1/trends/${trendId}/review`, data);
  },
};
