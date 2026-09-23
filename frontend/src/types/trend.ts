/**
 * Trend, Evidence, and Signals DTOs
 */

export type TrendStatus =
  | 'discovered'
  | 'analyzed'
  | 'scored'
  | 'prompt_generated'
  | 'pending_review'
  | 'approved'
  | 'rejected'
  | 'archived';

export type TrendCategory =
  | 'ai_visual'
  | 'product_marketing'
  | 'lifestyle'
  | 'entertainment'
  | 'education'
  | 'fashion'
  | 'food'
  | 'technology'
  | 'travel'
  | 'fitness'
  | 'other';

export interface TrendSignal {
  signal_type: string;
  raw_value: number;
  normalized_value: number;
  weight: number;
  weighted_score: number;
  source?: string;
}

export interface TrendEvidence {
  id: string;
  trend_candidate_id: string;
  platform: string;
  relevance_score?: number;
  created_at: string;
}

export interface PromptPackageSummary {
  id: string;
  version: number;
  quality_score?: number;
  validation_status?: string;
  generated_at?: string;
}

export interface TrendReviewSummary {
  id: string;
  reviewer_name?: string;
  decision: string;
  notes?: string;
  created_at: string;
}

export interface TrendListItem {
  id: string;
  title: string;
  category?: string;
  status: TrendStatus;
  overall_score?: number;
  risk_level?: string;
  first_seen_at?: string;
  last_seen_at?: string;
  created_at: string;
}

export interface TrendDetail extends TrendListItem {
  description?: string;
  core_concept?: string;
  updated_at: string;
  signals: TrendSignal[];
  evidence: TrendEvidence[];
  latest_prompt_package?: PromptPackageSummary;
  reviews: TrendReviewSummary[];
}

export interface TrendQueryParams {
  status?: string;
  category?: string;
  source?: string;
  minimum_score?: number;
  language?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
