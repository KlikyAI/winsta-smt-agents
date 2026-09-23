import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, Workspace } from '../types/auth';
import { authApi } from '../api/auth';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  workspaces: Workspace[];
  selectedWorkspaceId: string | null;
  selectWorkspace: (workspaceId: string) => void;
  createWorkspace: (name: string, slug?: string) => Promise<Workspace>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('user_profile');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('access_token');
  });

  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(() => (
    localStorage.getItem('selected_organization_id')
  ));

  const syncWorkspaces = async () => {
    const response = await authApi.listWorkspaces();
    const available = response.data || [];
    setWorkspaces(available);
    const stored = localStorage.getItem('selected_organization_id');
    const selected = available.find((workspace) => workspace.id === stored) || available[0];
    if (selected) {
      localStorage.setItem('selected_organization_id', selected.id);
      setSelectedWorkspaceId(selected.id);
    } else {
      localStorage.removeItem('selected_organization_id');
      setSelectedWorkspaceId(null);
    }
  };

  // Sync state changes with localStorage
  useEffect(() => {
    if (user && token) {
      localStorage.setItem('user_profile', JSON.stringify(user));
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('user_profile');
      localStorage.removeItem('access_token');
    }
  }, [user, token]);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    let active = true;
    authApi.getMe()
      .then((response) => {
        if (!active) return;
        setUser(response.data);
        setToken(localStorage.getItem('access_token'));
        return syncWorkspaces();
      })
      .catch(() => {
        if (active) logout();
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authApi.login({ email, password });
      const { user: loggedInUser, tokens } = response.data;
      setUser(loggedInUser);
      setToken(tokens.access_token);
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      localStorage.setItem('user_profile', JSON.stringify(loggedInUser));
      await syncWorkspaces();
    } catch (err: any) {
      logout();
      throw new Error(err.message || 'Authentication failed. Please verify email and password.');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_profile');
    localStorage.removeItem('selected_organization_id');
    setWorkspaces([]);
    setSelectedWorkspaceId(null);
  };

  useEffect(() => {
    const handleAuthExpired = () => logout();
    window.addEventListener('auth:expired', handleAuthExpired);
    return () => window.removeEventListener('auth:expired', handleAuthExpired);
  }, []);

  const selectWorkspace = (workspaceId: string) => {
    if (!workspaces.some((workspace) => workspace.id === workspaceId)) return;
    localStorage.setItem('selected_organization_id', workspaceId);
    setSelectedWorkspaceId(workspaceId);
  };

  const createWorkspace = async (name: string, slug?: string): Promise<Workspace> => {
    const response = await authApi.createWorkspace({ name, slug: slug || undefined });
    const workspace = response.data;
    setWorkspaces((current) => [...current, workspace]);
    localStorage.setItem('selected_organization_id', workspace.id);
    setSelectedWorkspaceId(workspace.id);
    return workspace;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!(user && token),
        isLoading,
        workspaces,
        selectedWorkspaceId,
        selectWorkspace,
        createWorkspace,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
