import { authApi } from '../api/auth';
import type { AuthResponse, LoginRequest, User, UserRole, Workspace } from '../types/auth';

export const authService = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const res = await authApi.login(credentials);
    return res.data;
  },

  register: async (payload: { email: string; password: string; full_name: string }): Promise<AuthResponse> => {
    const res = await authApi.register(payload);
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await authApi.getMe();
    return res.data;
  },

  listWorkspaces: async (): Promise<Workspace[]> => {
    const res = await authApi.listWorkspaces();
    return res.data;
  },

  createWorkspace: async (payload: { name: string; slug?: string }): Promise<Workspace> => {
    const res = await authApi.createWorkspace(payload);
    return res.data;
  },

  listUsers: async (search?: string): Promise<User[]> => {
    const res = await authApi.listUsers(search);
    return res.data;
  },

  createUser: async (payload: {
    email: string;
    password: string;
    full_name: string;
    role: UserRole;
  }): Promise<User> => {
    const res = await authApi.createUser(payload);
    return res.data;
  },

  updateUser: async (userId: string, payload: {
    full_name?: string;
    role?: UserRole;
    is_active?: boolean;
    password?: string;
  }): Promise<User> => {
    const res = await authApi.updateUser(userId, payload);
    return res.data;
  },
};

