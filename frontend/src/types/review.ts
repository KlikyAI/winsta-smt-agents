/**
 * Review / Approval DTOs
 */

export type ReviewDecision = 'approve' | 'reject' | 'request_regeneration';

export interface ReviewRequest {
  decision: ReviewDecision;
  notes?: string;
}

export interface TrendReview {
  id: string;
  trend_id: string;
  reviewer_id?: string;
  reviewer_name?: string;
  decision: ReviewDecision;
  notes?: string;
  created_at: string;
}
