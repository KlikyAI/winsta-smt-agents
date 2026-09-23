import { apiClient } from './client';
import type { AuthResponse, LoginRequest, User, UserRole, Workspace } from '../types/auth';
import type { ApiResponse } from '../types/common';

export const authApi = {
  login: async (credentials: LoginRequest): Promise<ApiResponse<AuthResponse>> => {
    return apiClient.post<AuthResponse>('/api/v1/auth/login', credentials);
  },

  register: async (payload: { email: string; password: string; full_name: string }): Promise<ApiResponse<AuthResponse>> => {
    return apiClient.post<AuthResponse>('/api/v1/auth/register', payload);
  },

  getMe: async (): Promise<ApiResponse<User>> => {
    return apiClient.get<User>('/api/v1/auth/me');
  },

  listWorkspaces: async (): Promise<ApiResponse<Workspace[]>> => {
    return apiClient.get<Workspace[]>('/api/v1/auth/workspaces');
  },

  createWorkspace: async (payload: { name: string; slug?: string }): Promise<ApiResponse<Workspace>> => {
    return apiClient.post<Workspace>('/api/v1/auth/workspaces', payload);
  },

  listUsers: async (search?: string): Promise<ApiResponse<User[]>> => {
    return apiClient.get<User[]>('/api/v1/auth/users', { search });
  },

  createUser: async (payload: {
    email: string;
    password: string;
    full_name: string;
    role: UserRole;
  }): Promise<ApiResponse<User>> => {
    return apiClient.post<User>('/api/v1/auth/users', payload);
  },

  updateUser: async (userId: string, payload: {
    full_name?: string;
    role?: UserRole;
    is_active?: boolean;
    password?: string;
  }): Promise<ApiResponse<User>> => {
    return apiClient.patch<User>(`/api/v1/auth/users/${userId}`, payload);
  },
};
