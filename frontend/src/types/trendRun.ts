/**
 * Trend Discovery Run DTOs
 */

export type TrendRunStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'partially_completed'
  | 'failed'
  | 'cancelled';

export interface CandidateItem {
  id: string;
  platform: string;
  status: string;
  title?: string;
  caption?: string;
  canonical_url?: string;
  author_name?: string;
  engagement_rate?: number;
  hashtags?: string[];
}

export interface TrendRun {
  id: string;
  status: TrendRunStatus;
  trigger_type: string;
  sources?: string[];
  categories?: string[];
  market?: string;
  language?: string;
  started_at?: string;
  completed_at?: string;
  candidate_count: number;
  accepted_count: number;
  rejected_count: number;
  error_count: number;
  metadata?: {
    platform_errors?: Record<string, string>;
    country?: string;
    category?: string;
    aesthetic?: string;
    time_window?: string;
    [key: string]: any;
  };
  candidates?: CandidateItem[];
  created_at: string;
  updated_at: string;
}

export interface CreateTrendRunRequest {
  sources?: string[];
  categories?: string[];
  market?: string;
  country?: string;
  category?: string;
  aesthetic?: string;
  time_window?: string;
  language?: string;
  limit_per_source?: number;
}
