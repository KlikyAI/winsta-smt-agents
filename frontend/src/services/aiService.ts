import { aiApi } from '../api/ai';
import type { AIProviderStatus, AIRuntimeSettings, AITestResponse, AIImageResponse } from '../api/ai';

export const aiService = {
  getProviders: async (): Promise<AIProviderStatus[]> => {
    const res = await aiApi.getProviders();
    return res.data;
  },

  getSettings: async (): Promise<AIRuntimeSettings> => {
    const res = await aiApi.getSettings();
    return res.data;
  },

  updateSettings: async (settings: Parameters<typeof aiApi.updateSettings>[0]): Promise<AIRuntimeSettings> => {
    const res = await aiApi.updateSettings(settings);
    return res.data;
  },

  testCompletion: async (payload: Parameters<typeof aiApi.testCompletion>[0]): Promise<AITestResponse> => {
    const res = await aiApi.testCompletion(payload);
    return res.data;
  },

  generateImage: async (payload: Parameters<typeof aiApi.generateImage>[0]): Promise<AIImageResponse> => {
    const res = await aiApi.generateImage(payload);
    return res.data;
  },

  /**
   * Stream completion tokens in real-time from the backend SSE endpoint.
   */
  async *streamCompletion(payload: {
    prompt: string;
    provider?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
  }): AsyncGenerator<string, void, unknown> {
    const token = localStorage.getItem('access_token');
    const orgId = localStorage.getItem('selected_organization_id');

    const response = await fetch('/api/v1/ai/generate/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(orgId ? { 'X-Organization-ID': orgId } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Streaming failed with status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data:')) continue;
        const rawJson = trimmed.replace(/^data:\s*/, '');
        if (rawJson === '[DONE]') return;

        try {
          const parsed = JSON.parse(rawJson);
          if (parsed.token) yield parsed.token;
          if (parsed.error) throw new Error(parsed.error);
        } catch (e: any) {
          if (e.message && e.message !== 'Unexpected token') throw e;
        }
      }
    }
  },
};

