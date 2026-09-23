export type SocialPlatform = 'instagram' | 'facebook' | 'tiktok' | 'youtube' | 'x' | 'linkedin' | 'threads';
export type SocialLanguage = 'id' | 'en' | 'ar';

export type SocialCampaignStatus = 'draft' | 'pending_approval' | 'approved' | 'rejected' | 'active' | 'paused' | 'completed';

export interface SocialCampaign {
  id: string;
  organization_id: string;
  created_by?: string;
  approved_by?: string;
  name: string;
  objective: string;
  platforms: string[];
  budget_cents: number;
  budget_type: 'daily' | 'lifetime' | string;
  currency: string;
  start_at?: string;
  end_at?: string;
  audience: Record<string, unknown>;
  creative_variant_ids: string[];
  brief_id?: string;
  notes?: string;
  provider_campaign_ids: Record<string, unknown>;
  status: SocialCampaignStatus | string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSocialCampaignRequest {
  name: string;
  objective: string;
  platforms: SocialPlatform[];
  budget_cents: number;
  budget_type?: 'daily' | 'lifetime';
  currency?: string;
  start_at?: string;
  end_at?: string;
  audience?: Record<string, unknown>;
  creative_variant_ids?: string[];
  brief_id?: string;
  notes?: string;
}

export type SocialBriefStatus =
  | 'queued'
  | 'generating'
  | 'ready_for_review'
  | 'completed'
  | 'failed';

export interface SocialBrief {
  id: string;
  organization_id: string;
  title: string;
  objective?: string;
  campaign_type: string;
  target_platforms: string[];
  target_audience?: string;
  tone?: string;
  language: string;
  target_languages: SocialLanguage[];
  status: SocialBriefStatus;
  source_trend_id?: string;
  source_prompt_package_id?: string;
  content_items: SocialContentItem[];
  created_at: string;
  updated_at: string;
}

export interface SocialContentItem {
  id: string;
  brief_id: string;
  concept?: string;
  status: string;
  ai_provider?: string;
  ai_model?: string;
  content_data?: Record<string, unknown>;
  variants: SocialContentVariant[];
}

export interface SocialContentVariant {
  id: string;
  platform: string;
  language: SocialLanguage;
  format?: string;
  aspect_ratio?: string;
  caption?: string;
  hook?: string;
  cta?: string;
  hashtags?: string[];
  media_ref?: string;
  media_asset_id?: string;
  visual_prompt?: string;
  generation_metadata?: Record<string, unknown>;
  version: number;
  qa_status: string;
  qa_result?: {
    status: string;
    score: number;
    checks: Record<string, boolean>;
    warnings?: string[];
  };
  status: string;
}

export interface SocialContentQueueItem extends SocialContentItem {
  brief_title: string;
  target_platforms: string[];
  created_at: string;
  updated_at: string;
}

export interface SocialPublishJob {
  id: string;
  content_variant_id: string;
  content_item_id: string;
  brief_title: string;
  platform: string;
  caption?: string;
  hook?: string;
  scheduled_at?: string;
  timezone: string;
  status: string;
  idempotency_key: string;
  attempt_count: number;
  max_attempts: number;
  next_attempt_at?: string;
  last_attempt_at?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewSocialContentRequest {
  decision: 'approve' | 'reject';
  notes?: string;
  variant_ids?: string[];
}

export interface ScheduleSocialContentRequest {
  scheduled_at?: string;
  variant_ids?: string[];
  timezone?: string;
}

export interface SocialConnectionAccount {
  id: string;
  platform: string;
  account_id: string;
  account_name?: string;
  scopes?: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SocialPlatformConnection {
  platform: SocialPlatform;
  display_name: string;
  description: string;
  setup_url: string;
  callback_url: string;
  requested_scopes: string[];
  status: 'connected' | 'configuration_required' | 'oauth_adapter_pending' | 'ready_to_authorize';
  missing_settings: string[];
  accounts: SocialConnectionAccount[];
}

export interface BeginSocialConnectionResult {
  platform: SocialPlatform;
  status: 'configuration_required' | 'oauth_adapter_pending' | 'ready_to_authorize';
  message: string;
  callback_url: string;
  authorization_url?: string;
  missing_settings: string[];
}

export interface SocialOAuthProviderDiagnostic {
  platform: SocialPlatform;
  display_name: string;
  server_configured: boolean;
  missing_settings: string[];
  manual_checks: string[];
}

export interface SocialOAuthDiagnostics {
  automatic_checks_passed: boolean;
  callback_url: string;
  frontend_return_url: string;
  callback_https: boolean;
  token_encryption_ready: boolean;
  issues: string[];
  providers: SocialOAuthProviderDiagnostic[];
}

export interface CreateSocialBriefRequest {
  title: string;
  objective?: string;
  campaign_type?: string;
  target_platforms: SocialPlatform[];
  target_audience?: string;
  tone?: string;
  language?: string;
  languages?: SocialLanguage[];
  source_trend_id?: string;
  source_prompt_package_id?: string;
  media_url?: string;
  generate_image?: boolean;
  image_model?: 'flux-realism' | 'dall-e-3';
  visual_prompt?: string;
}

export interface UpdateSocialVariantRequest {
  caption?: string;
  hook?: string;
  cta?: string;
  hashtags?: string[];
  media_ref?: string;
}

export interface RescheduleSocialPublishJobRequest {
  scheduled_at: string;
  timezone?: string;
}

export interface SocialMetricSnapshot {
  id: string;
  publish_job_id: string;
  platform: string;
  external_post_id: string;
  metrics: Record<string, unknown>;
  captured_at: string;
  created_at: string;
}

export interface SocialBrandKit {
  id: string;
  organization_id: string;
  version: number;
  brand_name: string;
  tagline?: string;
  logo_url?: string;
  colors: Record<string, string>;
  fonts: Record<string, string>;
  tone?: string;
  target_audience?: string;
  default_hashtags: string[];
  disclaimer?: string;
  forbidden_terms: string[];
  required_terms: string[];
  product_facts: Record<string, unknown>;
  languages: SocialLanguage[];
  guidelines?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type UpdateSocialBrandKitRequest = Omit<
  SocialBrandKit,
  'id' | 'organization_id' | 'version' | 'is_active' | 'created_at' | 'updated_at'
>;

export interface SocialPerformanceInsight {
  id: string;
  platform?: string;
  language?: string;
  content_format?: string;
  sample_size: number;
  performance_score: number;
  engagement_rate: number;
  confidence: number;
  summary: string;
  recommendations: Array<{
    action: string;
    priority: string;
    experiment?: {
      variable: string;
      control_publish_job_id: string;
      hypothesis: string;
      approval_required: boolean;
    };
  }>;
  evidence: Record<string, unknown>;
  status: string;
  analyzed_at: string;
  created_at: string;
}

export interface SocialMediaAsset {
  id: string;
  organization_id: string;
  content_item_id?: string;
  storage_bucket: string;
  storage_path: string;
  source_url?: string;
  signed_url?: string;
  mime_type: string;
  media_type: 'image' | 'video';
  size_bytes: number;
  sha256: string;
  provider?: string;
  prompt?: string;
  aspect_ratio?: string;
  status: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
