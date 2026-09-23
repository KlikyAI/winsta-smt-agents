import React, { useState, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { LanguageProvider } from './context/LanguageContext';
import { Layout } from './components/layout/Layout';
import { TriggerRunModal } from './components/domain/TriggerRunModal';
import { PageGuard } from './components/guards/PageGuard';
import { PageLoader } from './components/common/PageLoader';

// Dynamic route-level code-splitting by domain
const DashboardPage = lazy(() => import('./pages/dashboard/DashboardPage').then(m => ({ default: m.DashboardPage })));
const TrendsPage = lazy(() => import('./pages/trends/TrendsPage').then(m => ({ default: m.TrendsPage })));
const TrendRunsPage = lazy(() => import('./pages/trends/TrendRunsPage').then(m => ({ default: m.TrendRunsPage })));
const TrendSourcesPage = lazy(() => import('./pages/trends/TrendSourcesPage').then(m => ({ default: m.TrendSourcesPage })));
const ScoringPage = lazy(() => import('./pages/dashboard/ScoringPage').then(m => ({ default: m.ScoringPage })));
const LoginPage = lazy(() => import('./pages/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const SocialMediaPage = lazy(() => import('./pages/social/SocialMediaPage').then(m => ({ default: m.SocialMediaPage })));
const AdminPage = lazy(() => import('./pages/admin/AdminPage').then(m => ({ default: m.AdminPage })));
const SocialCampaignsPage = lazy(() => import('./pages/social/SocialCampaignsPage').then(m => ({ default: m.SocialCampaignsPage })));
const SocialAnalyticsPage = lazy(() => import('./pages/social/SocialAnalyticsPage').then(m => ({ default: m.SocialAnalyticsPage })));
const SocialApprovalsPage = lazy(() => import('./pages/social/SocialApprovalsPage').then(m => ({ default: m.SocialApprovalsPage })));
const SocialCalendarPage = lazy(() => import('./pages/social/SocialCalendarPage').then(m => ({ default: m.SocialCalendarPage })));
const SocialAccountsPage = lazy(() => import('./pages/social/SocialAccountsPage').then(m => ({ default: m.SocialAccountsPage })));
const PrivacyPage = lazy(() => import('./pages/legal/PrivacyPage').then(m => ({ default: m.PrivacyPage })));
const TermsPage = lazy(() => import('./pages/legal/TermsPage').then(m => ({ default: m.TermsPage })));
const DataDeletionPage = lazy(() => import('./pages/legal/DataDeletionPage').then(m => ({ default: m.DataDeletionPage })));
const LandingPage = lazy(() => import('./pages/auth/LandingPage').then(m => ({ default: m.LandingPage })));

const AuthenticatedRoutes: React.FC = () => {
  const [isTriggerModalOpen, setIsTriggerModalOpen] = useState(false);

  return (
    <Layout onTriggerRun={() => setIsTriggerModalOpen(true)}>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route
            path="/"
            element={<DashboardPage onTriggerRun={() => setIsTriggerModalOpen(true)} />}
          />
          <Route
            path="/dashboard"
            element={<DashboardPage onTriggerRun={() => setIsTriggerModalOpen(true)} />}
          />
          <Route
            path="/trends"
            element={<TrendsPage onTriggerRun={() => setIsTriggerModalOpen(true)} />}
          />
          <Route
            path="/runs"
            element={<TrendRunsPage onTriggerRun={() => setIsTriggerModalOpen(true)} />}
          />
          <Route path="/sources" element={<TrendSourcesPage />} />
          <Route path="/scoring" element={<ScoringPage />} />
          <Route path="/social" element={<SocialMediaPage />} />
          <Route path="/social/calendar" element={<SocialCalendarPage />} />
          <Route path="/social/approvals" element={<SocialApprovalsPage />} />
          <Route path="/social/accounts" element={<SocialAccountsPage />} />
          <Route path="/social/analytics" element={<SocialAnalyticsPage />} />
          <Route path="/social/campaigns" element={<SocialCampaignsPage />} />
          <Route
            path="/admin"
            element={
              <PageGuard requireAdmin>
                <AdminPage section="ai_engine" />
              </PageGuard>
            }
          />
          <Route
            path="/admin/ai-engine"
            element={
              <PageGuard requireAdmin>
                <AdminPage section="ai_engine" />
              </PageGuard>
            }
          />
          <Route
            path="/admin/users"
            element={
              <PageGuard requireAdmin>
                <AdminPage section="users" />
              </PageGuard>
            }
          />
          <Route
            path="/admin/brand-kit"
            element={
              <PageGuard requireAdmin>
                <AdminPage section="brand_kit" />
              </PageGuard>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <PageGuard requireAdmin>
                <AdminPage section="settings" />
              </PageGuard>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>

      <TriggerRunModal
        isOpen={isTriggerModalOpen}
        onClose={() => setIsTriggerModalOpen(false)}
        onRunCreated={() => {
          // Callback upon run creation
        }}
      />
    </Layout>
  );
};

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm font-semibold text-slate-500">Restoring secure session…</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AuthenticatedRoutes />;
};

const PublicLandingRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm font-semibold text-slate-500">Loading…</div>;
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />;
};

const PublicLoginRoute: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm font-semibold text-slate-500">Restoring secure session…</div>;
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage onSuccess={() => {}} />;
};

export default function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <ToastProvider>
            <Suspense fallback={<PageLoader message="Loading application..." />}>
              <Routes>
                {/* Public Legal & Provider Verification Routes */}
                <Route path="/" element={<PublicLandingRoute />} />
                <Route path="/landing" element={<PublicLandingRoute />} />
                <Route path="/login" element={<PublicLoginRoute />} />
                <Route path="/privacy" element={<PrivacyPage />} />
                <Route path="/terms" element={<TermsPage />} />
                <Route path="/data-deletion" element={<DataDeletionPage />} />

                {/* Main Authenticated Application Routes */}
                <Route path="/*" element={<AppContent />} />
              </Routes>
            </Suspense>
          </ToastProvider>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}
