import { apiClient } from './client';
import type { ApiResponse } from '../types/common';

export interface AIModelInfo {
  id: string;
  name: string;
  speed: string;
  capability: string;
}

export interface AIProviderStatus {
  provider: string;
  is_configured: boolean;
  is_active: boolean;
  is_fallback: boolean;
  default_model: string;
  models: AIModelInfo[];
}

export interface AIRuntimeSettings {
  ai_provider: string;
  ai_model: string;
  ai_fallback_provider: string;
  ai_fallback_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
  custom_keys_configured: Record<string, boolean>;
}

export interface AITestResponse {
  content: string;
  provider: string;
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
}

export interface AIImageResponse {
  image_url: string;
  trend_reference_image_url?: string;
  provider: string;
  model: string;
  prompt: string;
  latency_ms: number;
  aspect_ratio: string;
}

export const aiApi = {
  getProviders: async (): Promise<ApiResponse<AIProviderStatus[]>> => {
    return apiClient.get<AIProviderStatus[]>('/api/v1/ai/providers');
  },

  getSettings: async (): Promise<ApiResponse<AIRuntimeSettings>> => {
    return apiClient.get<AIRuntimeSettings>('/api/v1/ai/settings');
  },

  updateSettings: async (data: {
    ai_provider?: string;
    ai_model?: string;
    ai_fallback_provider?: string;
    ai_fallback_model?: string;
    ai_temperature?: number;
    ai_max_tokens?: number;
    deepseek_api_key?: string;
    openai_api_key?: string;
    anthropic_api_key?: string;
    gemini_api_key?: string;
    groq_api_key?: string;
    openrouter_api_key?: string;
  }): Promise<ApiResponse<AIRuntimeSettings>> => {
    return apiClient.put<AIRuntimeSettings>('/api/v1/ai/settings', data);
  },

  testCompletion: async (data: {
    prompt: string;
    provider?: string;
    model?: string;
  }): Promise<ApiResponse<AITestResponse>> => {
    return apiClient.post<AITestResponse>('/api/v1/ai/generate', data);
  },

  generateImage: async (data: {
    prompt_package_id: string;
    prompt: string;
    aspect_ratio?: string;
    model?: string;
  }): Promise<ApiResponse<AIImageResponse>> => {
    return apiClient.post<AIImageResponse>('/api/v1/ai/generate-image', data);
  },
};
