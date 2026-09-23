import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Check, Clipboard, ExternalLink, KeyRound, Link2, RefreshCw, ShieldCheck, Wrench } from 'lucide-react';
import { socialMediaApi } from '../../api/socialMedia';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Modal } from '../../components/common/Modal';
import { PlatformLogo } from '../../components/common/PlatformLogo';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import type { BeginSocialConnectionResult, SocialOAuthDiagnostics, SocialPlatform, SocialPlatformConnection } from '../../types/socialMedia';

const statusLabel: Record<SocialPlatformConnection['status'], string> = {
  connected: 'Connected',
  configuration_required: 'Setup required',
  oauth_adapter_pending: 'OAuth adapter pending',
  ready_to_authorize: 'Ready to connect',
};

const statusClass: Record<SocialPlatformConnection['status'], string> = {
  connected: 'bg-[#8b5cf6] text-[#0f172a]',
  configuration_required: 'bg-[#fff0d6] text-[#8a5200]',
  oauth_adapter_pending: 'bg-[#e0f2fe] text-[#075985]',
  ready_to_authorize: 'bg-[#8b5cf6] text-[#0f172a]',
};

export const SocialAccountsPage: React.FC = () => {
  const [providers, setProviders] = useState<SocialPlatformConnection[]>([]);
  const [selected, setSelected] = useState<SocialPlatformConnection | null>(null);
  const [readiness, setReadiness] = useState<BeginSocialConnectionResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChecking, setIsChecking] = useState(false);
  const [diagnostics, setDiagnostics] = useState<SocialOAuthDiagnostics | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const { user } = useAuth();
  const { addToast } = useToast();
  const canManageConnections = user?.role === 'admin';

  const loadConnections = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await socialMediaApi.getConnections();
      setProviders(response.data || []);
    } catch (error) {
      addToast('error', 'Unable to load social accounts', error instanceof Error ? error.message : undefined);
    } finally {
      setIsLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const connectionStatus = params.get('connection');
    if (connectionStatus === 'success') {
      addToast('success', 'Social Account Connected', 'Your social account has been authenticated and linked successfully.');
      window.history.replaceState({}, document.title, window.location.pathname);
      loadConnections();
    } else if (connectionStatus === 'error') {
      const reason = params.get('reason') || 'connection_failed';
      const platform = params.get('platform');
      const reasonMessages: Record<string, string> = {
        invalid_state: 'The authorization session expired or was already used. Start a new connection.',
        provider_denied: 'Authorization was cancelled or denied in the provider window.',
        no_manageable_account: 'The provider returned no Page, channel, or professional account that this app can publish to.',
        missing_permissions: 'Meta did not grant every required permission. Update the Facebook Login for Business configuration, then reconnect.',
        scope_not_authorized: 'TikTok did not authorize the requested scope. Enable user.info.basic for this Sandbox app and target user, revoke the previous authorization, then reconnect.',
        provider_response_invalid: 'The provider response did not include a publishable account.',
        provider_exchange_failed: 'The provider rejected the token exchange. Verify the exact callback URL, app mode, products, and approved scopes.',
        connection_failed: 'The connection could not be completed. Run OAuth diagnostics and try again.',
      };
      addToast('error', `${platform ? `${platform.toUpperCase()} ` : ''}Connection Failed`, reasonMessages[reason] || reasonMessages.connection_failed);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [addToast, loadConnections]);

  const openSetup = (provider: SocialPlatformConnection) => {
    setReadiness(null);
    setSelected(provider);
  };

  const handleConnect = async (platform: SocialPlatform) => {
    if (!canManageConnections) {
      addToast('error', 'Admin access required', 'Your authenticated backend role cannot manage OAuth connections.');
      return;
    }
    setSelected(providers.find((provider) => provider.platform === platform) || null);
    setIsChecking(true);
    try {
      const response = await socialMediaApi.beginConnection(platform);
      setReadiness(response.data);
      if (response.data.authorization_url) {
        window.location.assign(response.data.authorization_url);
        return;
      }
      addToast(
        response.data.status === 'configuration_required' ? 'info' : 'success',
        response.data.status === 'configuration_required' ? 'Backend setup is required' : 'Provider configuration detected',
        response.data.message,
      );
    } catch (error) {
      addToast('error', 'Unable to start authorization', error instanceof Error ? error.message : undefined);
    } finally {
      setIsChecking(false);
    }
  };

  const loadDiagnostics = async () => {
    try {
      const response = await socialMediaApi.getConnectionDiagnostics();
      setDiagnostics(response.data);
      setShowDiagnostics(true);
    } catch (error) {
      addToast('error', 'Unable to run OAuth diagnostics', error instanceof Error ? error.message : undefined);
    }
  };

  const copyCallback = async (callbackUrl: string) => {
    await navigator.clipboard.writeText(callbackUrl);
    addToast('success', 'Callback URL copied');
  };

  const connectedCount = providers.reduce((count, provider) => count + provider.accounts.filter((account) => account.status === 'connected').length, 0);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0f172a] p-8 text-[#ffffff]">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#1e293b] px-3 py-1 text-xs font-semibold"><Link2 className="h-3.5 w-3.5 text-[#7dd3fc]" /> Platform Connections</div>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Social Accounts</h2>
            <p className="mt-2 max-w-2xl text-sm text-[#cbd5e1]">Connect authorized publishing accounts through a server-owned OAuth flow. Tokens and client secrets never enter the browser.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {canManageConnections && <Button variant="light" size="sm" onClick={loadDiagnostics} leftIcon={<Wrench className="h-4 w-4" />}>Run diagnostics</Button>}
            <Button variant="light" size="sm" onClick={loadConnections} leftIcon={<RefreshCw className="h-4 w-4" />}>Refresh</Button>
          </div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        {[
          ['1', 'Configure app', 'Create the provider developer application.'],
          ['2', 'Register callback', 'Use the exact backend callback URL.'],
          ['3', 'Authorize', 'The account owner reviews requested scopes.'],
          ['4', 'Publish safely', 'The worker uses a server-side credential reference.'],
        ].map(([number, title, description]) => (
          <Card key={number} className="bg-white p-4">
            <div className="mb-3 flex h-7 w-7 items-center justify-center rounded-full bg-[#0f172a] text-xs font-black text-white">{number}</div>
            <p className="text-sm font-bold">{title}</p>
            <p className="mt-1 text-xs leading-relaxed text-[#64748b]">{description}</p>
          </Card>
        ))}
      </div>

      <div className="flex items-center gap-3 rounded-2xl border border-[#e2e8f0] bg-[#f1f5f9] px-4 py-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-[#8b5cf6]" />
        <p className="text-xs text-[#64748b]"><strong className="text-[#0f172a]">{connectedCount} connected account{connectedCount === 1 ? '' : 's'}.</strong> Publishing remains blocked for every platform without a verified connection.</p>
      </div>

      {!canManageConnections && (
        <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <p className="text-xs"><strong>Read-only access.</strong> Connecting and reconnecting providers requires the admin role on your authenticated backend account.</p>
        </div>
      )}

      {isLoading ? (
        <Card className="bg-white p-10 text-center text-sm text-[#64748b]">Loading platform connections…</Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {providers.map((provider) => (
            <Card key={provider.platform} className="bg-white p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <PlatformLogo platform={provider.platform} size="lg" />
                    <div><h3 className="font-bold">{provider.display_name}</h3><p className="text-[10px] font-semibold uppercase tracking-wider text-[#94a3b8]">{provider.accounts.length} account{provider.accounts.length === 1 ? '' : 's'}</p></div>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-[9px] font-black uppercase ${statusClass[provider.status]}`}>{statusLabel[provider.status]}</span>
                </div>
                <p className="mt-4 min-h-10 text-xs leading-relaxed text-[#64748b]">{provider.description}</p>
                {provider.accounts.map((account) => (
                  <div key={account.id} className="mt-3 flex items-center gap-2 rounded-xl bg-[#f8fafc] px-3 py-2 text-xs"><Check className="h-3.5 w-3.5 text-[#68a600]" /><span className="font-bold">{account.account_name || account.account_id}</span></div>
                ))}
              </div>
              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center gap-2">
                <Button className="flex-1" variant={provider.status === 'connected' ? 'secondary' : 'lime'} size="sm" onClick={() => handleConnect(provider.platform)} disabled={!canManageConnections} isLoading={isChecking && selected?.platform === provider.platform} leftIcon={<ExternalLink className="h-4 w-4" />}>
                  {provider.status === 'connected' ? 'Reconnect' : `Connect ${provider.display_name}`}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => openSetup(provider)} title="View OAuth settings">
                  <KeyRound className="h-4 w-4 text-slate-500" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={Boolean(selected)}
        onClose={() => setSelected(null)}
        title={selected ? `Connect ${selected.display_name}` : 'Connect account'}
        description="Provider credentials stay on the backend. Only connection metadata is shown here."
        maxWidth="xl"
        footer={selected && (
          <div className="flex flex-wrap justify-end gap-2">
            <a href={selected.setup_url} target="_blank" rel="noreferrer">
              <Button variant="secondary" leftIcon={<ExternalLink className="h-4 w-4" />}>Open developer portal</Button>
            </a>
            <Button variant="lime" disabled={!canManageConnections} isLoading={isChecking} onClick={() => handleConnect(selected.platform)} leftIcon={<ExternalLink className="h-4 w-4" />}>
              Connect with {selected.display_name}
            </Button>
          </div>
        )}
      >
        {selected && (
          <div className="space-y-5">
            <div>
              <p className="text-xs font-black uppercase tracking-wider text-[#64748b]">Required backend settings</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {selected.missing_settings.length ? selected.missing_settings.map((setting) => <code key={setting} className="rounded-lg bg-[#fff0d6] px-2 py-1 text-xs font-bold text-[#8a5200]">{setting}</code>) : <span className="inline-flex items-center gap-1 text-xs font-bold text-[#327000]"><Check className="h-3.5 w-3.5" /> Provider credentials detected</span>}
              </div>
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-wider text-[#64748b]">Exact callback URL</p>
              <div className="mt-2 flex items-center gap-2 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-3"><code className="min-w-0 flex-1 break-all text-xs">{selected.callback_url}</code><button type="button" onClick={() => copyCallback(selected.callback_url)} className="rounded-lg p-2 hover:bg-[#f1f5f9]" aria-label="Copy callback URL"><Clipboard className="h-4 w-4" /></button></div>
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-wider text-[#64748b]">Requested permissions</p>
              <div className="mt-2 flex flex-wrap gap-2">{selected.requested_scopes.map((scope) => <code key={scope} className="rounded-lg bg-[#f1f5f9] px-2 py-1 text-xs">{scope}</code>)}</div>
            </div>
            <div className="rounded-xl border border-[#f0c9ba] bg-[#fff2ed] p-4 text-xs leading-relaxed text-[#8f3515]">
              <strong>Security boundary:</strong> Authorization launches directly to the official {selected.display_name} OAuth consent window. Tokens and secrets are encrypted server-side and never enter localStorage.
            </div>
            {readiness && <div className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-4"><p className="text-xs font-black uppercase tracking-wider">Readiness result</p><p className="mt-2 text-sm">{readiness.message}</p></div>}
          </div>
        )}
      </Modal>

      <Modal
        isOpen={showDiagnostics}
        onClose={() => setShowDiagnostics(false)}
        title="OAuth connection diagnostics"
        description="Automatic checks inspect server configuration only. Provider portal approval remains a manual check."
        maxWidth="xl"
      >
        {diagnostics && (
          <div className="space-y-4">
            <div className={`rounded-xl border p-4 text-sm ${diagnostics.automatic_checks_passed ? 'border-emerald-200 bg-emerald-50 text-emerald-900' : 'border-amber-200 bg-amber-50 text-amber-900'}`}>
              <strong>{diagnostics.automatic_checks_passed ? 'Server checks passed.' : 'Server setup needs attention.'}</strong>
              <p className="mt-1 text-xs">Encryption: {diagnostics.token_encryption_ready ? 'ready' : 'invalid'} · HTTPS callback: {diagnostics.callback_https ? 'ready' : 'invalid'}</p>
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-wider text-[#64748b]">Exact callback for every provider</p>
              <div className="mt-2 flex items-center gap-2 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-3"><code className="min-w-0 flex-1 break-all text-xs">{diagnostics.callback_url}</code><button type="button" onClick={() => copyCallback(diagnostics.callback_url)} className="rounded-lg p-2 hover:bg-[#f1f5f9]" aria-label="Copy callback URL"><Clipboard className="h-4 w-4" /></button></div>
            </div>
            {diagnostics.issues.map((issue) => <p key={issue} className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-800">{issue}</p>)}
            <div className="grid gap-3 sm:grid-cols-2">
              {diagnostics.providers.map((provider) => (
                <div key={provider.platform} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-2"><strong className="text-sm">{provider.display_name}</strong><span className={`rounded-full px-2 py-1 text-[9px] font-black uppercase ${provider.server_configured ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>{provider.server_configured ? 'server configured' : 'missing settings'}</span></div>
                  {provider.missing_settings.length > 0 && <p className="mt-2 break-words text-xs text-amber-800">{provider.missing_settings.join(', ')}</p>}
                  <ul className="mt-3 list-disc space-y-1 pl-4 text-[11px] leading-relaxed text-slate-600">{provider.manual_checks.map((check) => <li key={check}>{check}</li>)}</ul>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
