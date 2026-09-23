/**
 * Base HTTP API client for communicating with the FastAPI backend
 */

import type { ApiResponse } from '../types/common';

const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : '';

class ApiClient {
  private baseUrl: string;
  private refreshPromise: Promise<string | null> | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeader(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    const organizationId = localStorage.getItem('selected_organization_id');
    return {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(organizationId ? { 'X-Organization-ID': organizationId } : {}),
    };
  }

  private async getFreshToken(): Promise<string | null> {
    if (this.refreshPromise) return this.refreshPromise;
    this.refreshPromise = (async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return null;
      const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok || !(response.headers.get('content-type') || '').includes('application/json')) return null;
      const data = await response.json();
      const accessToken = data?.data?.access_token;
      if (!accessToken) return null;
      localStorage.setItem('access_token', accessToken);
      if (data.data.refresh_token) localStorage.setItem('refresh_token', data.data.refresh_token);
      return accessToken;
    })().catch(() => null).finally(() => {
      this.refreshPromise = null;
    });
    return this.refreshPromise;
  }

  private handleAuthExpired(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_profile');
    localStorage.removeItem('selected_organization_id');
    window.dispatchEvent(new Event('auth:expired'));
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const isFormData = options.body instanceof FormData;
    let headers: Record<string, string> = {
      ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...this.getAuthHeader(),
      ...(options.headers as Record<string, string>),
    };

    try {
      let response = await fetch(url, {
        ...options,
        headers,
      });

      // If token expired or missing authorization, refresh once
      if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register') && !endpoint.includes('/auth/refresh')) {
        const freshToken = await this.getFreshToken();
        if (freshToken) {
          headers['Authorization'] = `Bearer ${freshToken}`;
          response = await fetch(url, {
            ...options,
            headers,
          });
        } else {
          this.handleAuthExpired();
        }
      }

      const contentType = response.headers.get('content-type') || '';
      let data: any;

      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        await response.text();
        if (!response.ok) {
          throw new Error(`Server returned status ${response.status} (${response.statusText || 'Endpoint unavailable'}). Please verify backend connection.`);
        }
        // If it returned HTML unexpectedly with 200
        throw new Error('Received non-JSON response from server. Please check backend proxy routing.');
      }

      if (!response.ok) {
        throw new Error(data?.message || data?.detail || `Request failed with status ${response.status}`);
      }

      return data as ApiResponse<T>;
    } catch (error: any) {
      console.error(`[API Error] ${endpoint}:`, error);
      throw error;
    }
  }

  get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }
    return this.request<T>(url, { method: 'GET' });
  }

  post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  postForm<T>(endpoint: string, body: FormData): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'POST', body });
  }

  patch<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
