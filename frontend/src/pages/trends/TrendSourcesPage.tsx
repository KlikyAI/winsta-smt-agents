import React, { useState, useEffect } from 'react';
import {
  Share2,
  RefreshCw,
  Power,
  Key,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PlatformLogo } from '../../components/common/PlatformLogo';
import { ConfigureSourceModal } from '../../components/domain/ConfigureSourceModal';
import type { TrendSource } from '../../types/trendSource';
import { trendSourcesApi } from '../../api/trendSources';
import { useToast } from '../../context/ToastContext';

export const TrendSourcesPage: React.FC = () => {
  const { addToast } = useToast();
  const [sources, setSources] = useState<TrendSource[]>([]);
  const [selectedSourceForConfig, setSelectedSourceForConfig] = useState<TrendSource | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSources = async () => {
    setIsLoading(true);
    try {
      const res = await trendSourcesApi.getSources();
      setSources(res.data || []);
    } catch (err: any) {
      addToast('error', 'Failed to load trend sources', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleToggle = async (source: TrendSource) => {
    try {
      if (source.enabled) {
        await trendSourcesApi.disableSource(source.id);
        addToast('info', 'Source Paused', `${source.name} collection is now paused.`);
      } else {
        await trendSourcesApi.enableSource(source.id);
        addToast('success', 'Source Activated', `${source.name} is now actively scraping.`);
      }
      fetchSources();
    } catch (err: any) {
      addToast('error', 'Update Failed', err.message);
    }
  };

  const hasCredentialsConfigured = (source: TrendSource) => {
    if (!source.configuration) return false;
    const cfg = source.configuration;
    return Boolean(
      cfg.client_id ||
      cfg.app_id ||
      cfg.client_key ||
      cfg.api_key ||
      cfg.access_token ||
      cfg.bearer_token
    );
  };

  const formatPlatformName = (platform: string) => {
    return platform
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-[#0f172a] text-[#8b5cf6] flex items-center justify-center shadow-xs">
              <Share2 className="w-4 h-4" />
            </span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Platform Sources
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Configure multi-platform scraper & API credentials (Instagram, TikTok, YouTube Shorts, X, Google Trends, LinkedIn).
          </p>
        </div>

        <Button
          variant="light"
          size="sm"
          onClick={fetchSources}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {sources.map((source) => {
          const isConfigured = hasCredentialsConfigured(source);
          return (
            <Card
              key={source.id}
              className="p-6 bg-white rounded-3xl border border-slate-200 hover:border-[#8b5cf6] shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Top Row: Logo & Status Badges */}
                <div className="flex items-start justify-between gap-2">
                  <PlatformLogo platform={source.platform} size="lg" />

                  <div className="flex items-center gap-1.5 flex-wrap justify-end">
                    {isConfigured ? (
                      <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Configured
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                        Default Engine
                      </span>
                    )}

                    <span
                      className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1 border ${
                        source.enabled
                          ? 'bg-purple-50 text-purple-700 border-purple-200'
                          : 'bg-slate-100 text-slate-500 border-slate-200'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          source.enabled ? 'bg-[#8b5cf6] animate-pulse' : 'bg-slate-400'
                        }`}
                      />
                      {source.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                </div>

                {/* Source Title & Meta */}
                <div className="mt-4">
                  <h3 className="text-base font-bold text-slate-900 leading-snug">
                    {source.name}
                  </h3>
                  <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                    <span>Platform: <strong className="text-slate-700 font-semibold">{formatPlatformName(source.platform)}</strong></span>
                    <span>•</span>
                    <span className="uppercase text-[11px] font-mono text-slate-500">{source.collector_type}</span>
                  </div>
                </div>

                {/* Security / Credential Status */}
                <div className="mt-4 py-2 px-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-600 font-medium">
                    <Lock className="w-3.5 h-3.5 text-[#8b5cf6]" />
                    <span>PostgreSQL AES Encryption</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">
                    {source.last_sync_at ? `Synced ${new Date(source.last_sync_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Ready'}
                  </span>
                </div>
              </div>

              {/* Footer Actions */}
              <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <Button
                  variant="light"
                  size="sm"
                  onClick={() => setSelectedSourceForConfig(source)}
                  leftIcon={<Key className="w-3.5 h-3.5 text-[#8b5cf6]" />}
                >
                  Configure Keys
                </Button>

                <Button
                  variant={source.enabled ? 'light' : 'primary'}
                  size="sm"
                  onClick={() => handleToggle(source)}
                  leftIcon={<Power className={`w-3.5 h-3.5 ${source.enabled ? 'text-rose-500' : 'text-emerald-400'}`} />}
                >
                  {source.enabled ? 'Pause' : 'Activate'}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Configure Credentials Modal */}
      <ConfigureSourceModal
        source={selectedSourceForConfig}
        isOpen={!!selectedSourceForConfig}
        onClose={() => setSelectedSourceForConfig(null)}
        onSuccess={fetchSources}
      />
    </div>
  );
};
