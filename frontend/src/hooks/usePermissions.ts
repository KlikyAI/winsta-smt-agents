import { useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types/auth';

export function usePermissions() {
  const { user, workspaces, selectedWorkspaceId } = useAuth();

  const currentWorkspace = useMemo(() => {
    return workspaces.find((w) => w.id === selectedWorkspaceId) || null;
  }, [workspaces, selectedWorkspaceId]);

  const userRole = user?.role || null;
  const workspaceRole = currentWorkspace?.role || null;

  const isAdmin = userRole === 'admin' || workspaceRole === 'owner' || workspaceRole === 'admin';
  const isManager = isAdmin || userRole === 'trend_manager';
  const canReview = isManager || userRole === 'reviewer';

  const hasRole = (allowedRoles: UserRole[]): boolean => {
    if (!userRole) return false;
    if (isAdmin) return true; // Admins satisfy any permission
    return allowedRoles.includes(userRole);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (isAdmin) return true;

    switch (permission) {
      case 'manage:settings':
      case 'manage:users':
      case 'manage:workspaces':
        return isAdmin;
      case 'manage:campaigns':
      case 'manage:publish':
      case 'trigger:runs':
        return isManager;
      case 'review:trends':
      case 'approve:content':
        return canReview;
      case 'view:analytics':
      case 'view:trends':
      default:
        return true;
    }
  };

  return {
    user,
    userRole,
    workspaceRole,
    currentWorkspace,
    isAdmin,
    isManager,
    canReview,
    hasRole,
    hasPermission,
  };
}

