import React, { useState, useEffect } from 'react';
import { PlayCircle, RefreshCw, XCircle, Eye, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { TrendRunStatusBadge } from '../../components/common/Badge';
import { TrendRunDetailModal } from '../../components/domain/TrendRunDetailModal';
import type { TrendRun } from '../../types/trendRun';
import { trendRunsApi } from '../../api/trendRuns';
import { useToast } from '../../context/ToastContext';
import { useLanguage } from '../../context/LanguageContext';
import { COUNTRIES } from '../../constants/discoveryOptions';

interface TrendRunsPageProps {
  onTriggerRun: () => void;
}

export const TrendRunsPage: React.FC<TrendRunsPageProps> = ({ onTriggerRun }) => {
  const { addToast } = useToast();
  const { t } = useLanguage();
  const [runs, setRuns] = useState<TrendRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<TrendRun | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRuns, setTotalRuns] = useState(0);
  const pageSize = 10;

  // Timer counter for active row animations
  const [tick, setTick] = useState(0);

  const fetchRuns = async (showLoading = false, pageToFetch = page) => {
    if (showLoading) setIsRefreshing(true);
    try {
      const res = await trendRunsApi.getRuns(pageToFetch, pageSize);
      setRuns(res.data?.items || []);
      setTotalPages(Math.max(res.data?.total_pages || 1, 1));
      setTotalRuns(res.data?.total || 0);
    } catch (err: any) {
      addToast('error', 'Failed to fetch discovery runs', err.message);
    } finally {
      if (showLoading) setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRuns(false, page);
    // Fast polling every 3 seconds for live row tracking
    const interval = setInterval(() => {
      fetchRuns(false, page);
      setTick((t) => t + 1);
    }, 3000);
    return () => clearInterval(interval);
  }, [page]);

  const handleOpenDetail = async (runItem: TrendRun) => {
    try {
      const res = await trendRunsApi.getRunById(runItem.id);
      setSelectedRun(res.data || runItem);
    } catch {
      setSelectedRun(runItem);
    }
  };

  const handleCancel = async (runId: string) => {
    try {
      await trendRunsApi.cancelRun(runId);
      addToast('info', 'Run Cancelled', 'Discovery run has been stopped.');
      fetchRuns(false, page);
    } catch (err: any) {
      addToast('error', 'Cancellation Failed', err.message);
    }
  };

  const getLiveRowStage = (tickVal: number) => {
    const step = tickVal % 4;
    if (step === 0) return t('stage.connecting', 'Connecting APIs...');
    if (step === 1) return t('stage.ingesting', 'Ingesting posts...');
    if (step === 2) return t('stage.scoring', 'Scoring signals...');
    return t('stage.synthesizing', 'Synthesizing prompts...');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-[#0f172a] text-[#8b5cf6] flex items-center justify-center">
              <PlayCircle className="w-4 h-4 fill-current" />
            </span>
            <h2 className="text-2xl font-bold text-[#0f172a] tracking-tight">
              {t('runs.title', 'Trend Discovery Runs')}
            </h2>
          </div>
          <p className="text-xs text-[#64748b] mt-1 font-medium">
            {t('runs.subtitle', 'Monitor real-time asynchronous multi-queue discovery jobs dispatched to Celery.')}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="light"
            size="sm"
            onClick={() => fetchRuns(true)}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            {t('runs.refresh', 'Refresh')}
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={onTriggerRun}
            leftIcon={<PlayCircle className="w-4 h-4 text-[#8b5cf6]" />}
          >
            {t('runs.launch', 'Launch Discovery Run')}
          </Button>
        </div>
      </div>

      {/* Runs Table / List */}
      <Card className="overflow-hidden p-0 border bg-[#ffffff]">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-[#f8fafc] text-[#0f172a] uppercase tracking-wider font-bold border-b border-[#e2e8f0]">
              <tr>
                <th className="px-6 py-4">{t('runs.col.id', 'Run ID')}</th>
                <th className="px-6 py-4">{t('runs.col.status', 'Status & Live Progress')}</th>
                <th className="px-6 py-4">{t('runs.col.target', 'Target Region & Niche')}</th>
                <th className="px-6 py-4">{t('runs.col.sources', 'Sources')}</th>
                <th className="px-6 py-4">{t('runs.col.items', 'Items Discovered')}</th>
                <th className="px-6 py-4">{t('runs.col.started', 'Started At')}</th>
                <th className="px-6 py-4 text-right">{t('runs.col.actions', 'Actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e2e8f0]/60 bg-[#ffffff]">
              {runs.length > 0 ? (
                runs.map((run) => {
                  const countryCode = (run.metadata?.country || run.market || 'GLOBAL').toUpperCase();
                  const countryObj = COUNTRIES.find((c) => c.code === countryCode);
                  const categoryName = run.metadata?.category || (run.categories && run.categories[0]) || 'general';
                  const isRunActive = run.status === 'running' || run.status === 'queued';

                  return (
                    <tr
                      key={run.id}
                      onClick={() => handleOpenDetail(run)}
                      className={`transition-colors cursor-pointer ${
                        isRunActive
                          ? 'bg-[#8b5cf6]/10 hover:bg-[#8b5cf6]/20 font-semibold'
                          : 'hover:bg-[#f8fafc]/80'
                      }`}
                    >
                      {/* Run ID with in-row live spinner */}
                      <td className="px-6 py-4 font-mono font-bold text-[#0f172a]">
                        <div className="flex items-center gap-2">
                          {isRunActive ? (
                            <span className="relative flex h-2.5 w-2.5">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#8b5cf6] opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#8b5cf6]"></span>
                            </span>
                          ) : (
                            <span className="w-2 h-2 rounded-full bg-[#e2e8f0]" />
                          )}
                          <span dir="ltr">#{run.id.substring(0, 8)}...</span>
                        </div>
                      </td>

                      {/* Status & Per-Item Live Progress Bar */}
                      <td className="px-6 py-4">
                        {isRunActive ? (
                          <div className="space-y-1.5 min-w-[170px]">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-bold text-[#8b5cf6] flex items-center gap-1.5">
                                <Loader2 className="w-3 h-3 animate-spin" />
                                {getLiveRowStage(tick)}
                              </span>
                              <span className="font-mono text-[10px] text-[#64748b] font-bold">~5s</span>
                            </div>
                            <div className="w-full h-1.5 rounded-full bg-[#e2e8f0]/50 overflow-hidden">
                              <div className="h-full bg-[#8b5cf6] rounded-full animate-pulse w-3/4" />
                            </div>
                          </div>
                        ) : (
                          <TrendRunStatusBadge status={run.status} />
                        )}
                      </td>

                      {/* Target Region & Niche */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 font-bold text-[#0f172a]">
                          <span>{countryObj?.flag || '🌐'}</span>
                          <span>{countryObj?.name.split('/')[0].trim() || countryCode}</span>
                          <span className="px-1.5 py-0.5 rounded bg-[#f8fafc] border border-[#e2e8f0] text-[10px] text-[#64748b] font-normal capitalize">
                            {categoryName.replace('_', ' ')}
                          </span>
                        </div>
                      </td>

                      {/* Platform Sources */}
                      <td className="px-6 py-4 text-[#64748b] font-medium">
                        {run.sources && run.sources.length > 0 ? run.sources.join(', ') : t('runs.all_platforms', 'All Platforms')}
                      </td>

                      {/* Items Ingested Counter */}
                      <td className="px-6 py-4 font-bold text-[#0f172a]">
                        {isRunActive ? (
                          <span className="text-[#8b5cf6] flex items-center gap-1 text-xs">
                            <Loader2 className="w-3 h-3 animate-spin" /> Processing...
                          </span>
                        ) : (
                          <div className="flex items-center gap-1.5">
                            <span className={run.candidate_count > 0 ? 'text-[#0f172a]' : 'text-[#94a3b8]'}>
                              {run.candidate_count} {t('runs.items_count', 'items')}
                            </span>
                            {run.candidate_count > 0 && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#8b5cf6] text-[#ffffff] font-black">
                                {t('runs.ready', 'READY')}
                              </span>
                            )}
                          </div>
                        )}
                      </td>

                      {/* Started At Timestamp */}
                      <td className="px-6 py-4 text-[#64748b]">
                        <span dir="ltr">
                          {run.started_at ? new Date(run.started_at).toLocaleTimeString() : new Date(run.created_at).toLocaleTimeString()}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant={isRunActive ? 'primary' : 'light'}
                            size="sm"
                            onClick={() => handleOpenDetail(run)}
                            leftIcon={<Eye className="w-3.5 h-3.5" />}
                          >
                            {t('runs.inspect', 'Inspect Items')}
                          </Button>

                          {isRunActive && (
                            <Button
                              variant="danger"
                              size="sm"
                              onClick={() => handleCancel(run.id)}
                              leftIcon={<XCircle className="w-3.5 h-3.5" />}
                            >
                              {t('runs.cancel', 'Cancel')}
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-[#64748b] font-medium">
                    {t('runs.empty', 'No discovery runs recorded yet. Click "Launch Discovery Run" to start one.')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {totalPages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#64748b]">
          <span>
            {t('runs.page', 'Page')} {page} / {totalPages} · {totalRuns} {t('runs.total_runs', 'runs')}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="light"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((current) => Math.max(current - 1, 1))}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              {t('runs.previous', 'Previous')}
            </Button>
            <Button
              variant="light"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((current) => Math.min(current + 1, totalPages))}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              {t('runs.next', 'Next')}
            </Button>
          </div>
        </div>
      )}

      {/* Discovery Run Detail & Candidates Modal */}
      <TrendRunDetailModal
        run={selectedRun}
        isOpen={!!selectedRun}
        onClose={() => setSelectedRun(null)}
      />
    </div>
  );
};
