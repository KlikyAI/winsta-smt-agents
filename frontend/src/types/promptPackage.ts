/**
 * Prompt Package DTOs supporting 6 AI Modalities
 */

export interface PromptPackage {
  id: string;
  trend_id: string;
  version: number;
  trend_title: string;
  description?: string;
  core_concept?: string;
  category?: string;
  generation_modes?: string[];

  // 6 AI Modalities
  text_to_image_prompt?: string;
  image_prompt?: string;
  text_to_video_prompt?: string;
  text_to_voice_prompt?: string;
  image_to_image_prompt?: string;
  image_to_video_prompt?: string;
  video_to_video_prompt?: string;

  negative_prompt?: string;
  trend_reference_image_url?: string;
  tags?: string[];
  quality_score?: number;
  risk_flags?: string[];
  ai_provider?: string;
  ai_model?: string;
  template_version?: string;
  generated_at?: string;
  validation_status?: string;
  created_at: string;
  updated_at: string;
}
