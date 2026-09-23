import React from 'react';
import { Navigate, Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { usePermissions } from '../../hooks/usePermissions';
import type { UserRole } from '../../types/auth';

export interface PageGuardProps {
  requireAuth?: boolean;
  requireAdmin?: boolean;
  roles?: UserRole[];
  permission?: string;
  children: React.ReactNode;
}

export const PageGuard: React.FC<PageGuardProps> = ({
  requireAuth = true,
  requireAdmin = false,
  roles,
  permission,
  children,
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const { isAdmin, hasRole, hasPermission } = usePermissions();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-semibold text-slate-500">Memuat hak akses akun…</p>
        </div>
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const isDenied =
    (requireAdmin && !isAdmin) ||
    (roles && !hasRole(roles)) ||
    (permission && !hasPermission(permission));

  if (isDenied) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-slate-200 shadow-xl text-center flex flex-col items-center">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center mb-4">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Akses Dibatasi</h2>
          <p className="text-sm text-slate-500 mb-6">
            Akun Anda tidak memiliki izin yang memadai untuk melihat atau mengelola halaman ini. Silakan hubungi administrator workspace Anda.
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Kembali ke Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

