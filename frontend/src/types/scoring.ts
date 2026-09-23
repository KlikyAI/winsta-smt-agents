/**
 * Scoring DTOs
 */

export interface ScoringWeightItem {
  signal_type: string;
  weight: number;
  description?: string;
}

export interface ScoringSettings {
  weights: ScoringWeightItem[];
  total_weight: number;
  version: number;
}

export interface UpdateScoringSettingsRequest {
  weights: ScoringWeightItem[];
}
