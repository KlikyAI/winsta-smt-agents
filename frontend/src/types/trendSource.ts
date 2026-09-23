/**
 * Trend Source DTOs
 */

export interface TrendSource {
  id: string;
  name: string;
  platform: string;
  enabled: boolean;
  collector_type: string;
  last_sync_at?: string;
  created_at: string;
  updated_at: string;
  configuration?: Record<string, any>;
}

export interface UpdateTrendSourceRequest {
  name?: string;
  collector_type?: string;
  configuration?: Record<string, any>;
}
