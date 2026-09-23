import { apiClient } from './client';
import type { ApiResponse, PaginatedResponse } from '../types/common';
import type {
  CreateSocialBriefRequest,
  BeginSocialConnectionResult,
  ReviewSocialContentRequest,
  RescheduleSocialPublishJobRequest,
  ScheduleSocialContentRequest,
  SocialBrief,
  SocialContentItem,
  SocialContentQueueItem,
  SocialPlatform,
  SocialPlatformConnection,
  SocialPublishJob,
  SocialMetricSnapshot,
  SocialBrandKit,
  SocialCampaign,
  CreateSocialCampaignRequest,
  SocialMediaAsset,
  SocialPerformanceInsight,
  SocialOAuthDiagnostics,
  UpdateSocialBrandKitRequest,
  UpdateSocialVariantRequest,
} from '../types/socialMedia';

export const socialMediaApi = {
  createCampaign: (data: CreateSocialCampaignRequest): Promise<ApiResponse<SocialCampaign>> =>
    apiClient.post('/api/v1/social/campaigns', data),

  getCampaigns: (status?: string, page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<SocialCampaign>>> =>
    apiClient.get('/api/v1/social/campaigns', { status, page, page_size: pageSize }),

  getCampaign: (campaignId: string): Promise<ApiResponse<SocialCampaign>> =>
    apiClient.get(`/api/v1/social/campaigns/${campaignId}`),

  submitCampaign: (campaignId: string, notes?: string): Promise<ApiResponse<SocialCampaign>> =>
    apiClient.post(`/api/v1/social/campaigns/${campaignId}/submit`, notes ? { notes } : {}),

  approveCampaign: (campaignId: string, notes?: string): Promise<ApiResponse<SocialCampaign>> =>
    apiClient.post(`/api/v1/social/campaigns/${campaignId}/approve`, notes ? { notes } : {}),

  rejectCampaign: (campaignId: string, notes?: string): Promise<ApiResponse<SocialCampaign>> =>
    apiClient.post(`/api/v1/social/campaigns/${campaignId}/reject`, notes ? { notes } : {}),

  createBrief: (data: CreateSocialBriefRequest): Promise<ApiResponse<{ id: string; status: string }>> =>
    apiClient.post('/api/v1/social/briefs', data),

  getBriefs: (page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<SocialBrief>>> =>
    apiClient.get('/api/v1/social/briefs', { page, page_size: pageSize }),

  getBrief: (briefId: string): Promise<ApiResponse<SocialBrief>> =>
    apiClient.get(`/api/v1/social/briefs/${briefId}`),

  getContent: (status?: string, page = 1, pageSize = 50): Promise<ApiResponse<PaginatedResponse<SocialContentQueueItem>>> =>
    apiClient.get('/api/v1/social/content', { status, page, page_size: pageSize }),

  reviewContent: (contentId: string, data: ReviewSocialContentRequest): Promise<ApiResponse<SocialContentItem>> =>
    apiClient.post(`/api/v1/social/content/${contentId}/review`, data),

  scheduleContent: (contentId: string, data: ScheduleSocialContentRequest): Promise<ApiResponse<SocialPublishJob[]>> =>
    apiClient.post(`/api/v1/social/content/${contentId}/schedule`, data),

  updateVariant: (variantId: string, data: UpdateSocialVariantRequest): Promise<ApiResponse<SocialContentItem>> =>
    apiClient.patch(`/api/v1/social/variants/${variantId}`, data),

  getPublishJobs: (status?: string, page = 1, pageSize = 100): Promise<ApiResponse<PaginatedResponse<SocialPublishJob>>> =>
    apiClient.get('/api/v1/social/publish-jobs', { status, page, page_size: pageSize }),

  getAnalytics: (limit = 100): Promise<ApiResponse<SocialMetricSnapshot[]>> =>
    apiClient.get('/api/v1/social/analytics', { limit }),

  getBrandKit: (): Promise<ApiResponse<SocialBrandKit>> =>
    apiClient.get('/api/v1/social/brand-kit'),

  updateBrandKit: (data: UpdateSocialBrandKitRequest): Promise<ApiResponse<SocialBrandKit>> =>
    apiClient.put('/api/v1/social/brand-kit', data),

  getPerformanceInsights: (): Promise<ApiResponse<SocialPerformanceInsight[]>> =>
    apiClient.get('/api/v1/social/optimization/insights'),

  analyzePerformance: (): Promise<ApiResponse<SocialPerformanceInsight[]>> =>
    apiClient.post('/api/v1/social/optimization/analyze'),

  uploadAsset: (file: File): Promise<ApiResponse<SocialMediaAsset>> => {
    const form = new FormData();
    form.append('file', file);
    return apiClient.postForm('/api/v1/social/assets', form);
  },

  getAssets: (limit = 100): Promise<ApiResponse<SocialMediaAsset[]>> =>
    apiClient.get('/api/v1/social/assets', { limit }),

  refreshAssetUrl: (assetId: string): Promise<ApiResponse<SocialMediaAsset>> =>
    apiClient.post(`/api/v1/social/assets/${assetId}/signed-url`),

  getConnections: (): Promise<ApiResponse<SocialPlatformConnection[]>> =>
    apiClient.get('/api/v1/social/connections'),

  beginConnection: (platform: SocialPlatform): Promise<ApiResponse<BeginSocialConnectionResult>> =>
    apiClient.post(`/api/v1/social/connections/${platform}/begin`),

  getConnectionDiagnostics: (): Promise<ApiResponse<SocialOAuthDiagnostics>> =>
    apiClient.get('/api/v1/social/connections/diagnostics'),

  cancelPublishJob: (jobId: string): Promise<ApiResponse<SocialPublishJob>> =>
    apiClient.post(`/api/v1/social/publish-jobs/${jobId}/cancel`),

  retryPublishJob: (jobId: string): Promise<ApiResponse<SocialPublishJob>> =>
    apiClient.post(`/api/v1/social/publish-jobs/${jobId}/retry`),

  reschedulePublishJob: (jobId: string, data: RescheduleSocialPublishJobRequest): Promise<ApiResponse<SocialPublishJob>> =>
    apiClient.post(`/api/v1/social/publish-jobs/${jobId}/reschedule`, data),
};
