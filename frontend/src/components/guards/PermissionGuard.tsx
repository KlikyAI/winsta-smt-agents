import React from 'react';
import { usePermissions } from '../../hooks/usePermissions';
import type { UserRole } from '../../types/auth';

export interface PermissionGuardProps {
  permission?: string;
  roles?: UserRole[];
  requireAdmin?: boolean;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  roles,
  requireAdmin,
  fallback = null,
  children,
}) => {
  const { isAdmin, hasRole, hasPermission } = usePermissions();

  if (requireAdmin && !isAdmin) {
    return <>{fallback}</>;
  }

  if (roles && !hasRole(roles)) {
    return <>{fallback}</>;
  }

  if (permission && !hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

