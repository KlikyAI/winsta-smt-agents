import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, CheckCircle, Clock, PlayCircle, ArrowRight, Activity, Sparkles } from 'lucide-react';
import { StatCard } from '../../components/common/StatCard';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { TrendCard } from '../../components/domain/TrendCard';
import { TrendDetailModal } from '../../components/domain/TrendDetailModal';
import { ReviewActionModal } from '../../components/domain/ReviewActionModal';
import type { TrendListItem } from '../../types/trend';
import type { TrendRun } from '../../types/trendRun';
import { TrendRunStatusBadge } from '../../components/common/Badge';
import { trendsApi } from '../../api/trends';
import { trendRunsApi } from '../../api/trendRuns';
import { useLanguage } from '../../context/LanguageContext';

interface DashboardPageProps {
  onTriggerRun: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onTriggerRun }) => {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [trends, setTrends] = useState<TrendListItem[]>([]);
  const [runs, setRuns] = useState<TrendRun[]>([]);
  const [totalTrendsCount, setTotalTrendsCount] = useState<number>(0);
  const [selectedTrend, setSelectedTrend] = useState<TrendListItem | null>(null);
  const [reviewTrend, setReviewTrend] = useState<TrendListItem | null>(null);

  const loadData = async () => {
    try {
      const [trendsRes, runsRes] = await Promise.all([
        trendsApi.getTrends({ page_size: 6 }),
        trendRunsApi.getRuns(1, 4),
      ]);
      setTrends(trendsRes.data?.items || []);
      setTotalTrendsCount(trendsRes.data?.total || trendsRes.data?.items?.length || 0);
      setRuns(runsRes.data?.items || []);
    } catch (err) {
      console.warn('Using fallback data for dashboard:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const pendingCount = trends.filter((t) => t.status === 'pending_review' || t.status === 'prompt_generated').length;
  const approvedCount = trends.filter((t) => t.status === 'approved').length;

  return (
    <div className="space-y-8">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl p-8 md:p-10 bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f8fafc] border border-[#e2e8f0] text-xs font-semibold text-[#0f172a] mb-3">
            <Sparkles className="w-3.5 h-3.5 text-[#8b5cf6]" />
            <span>{t('hero.badge', 'Winsta AI Studio')}</span>
          </div>

          <h2 className="text-3xl md:text-4xl font-bold text-[#0f172a] tracking-tight leading-tight">
            {t('hero.title.pre', 'Trend Curation &')}{' '}
            <span className="underline decoration-[#8b5cf6] decoration-4 underline-offset-4">
              {t('hero.title.highlight', 'AI Prompt Studio')}
            </span>
          </h2>

          <p className="text-sm text-[#64748b] mt-3 leading-relaxed">
            {t('hero.subtitle', 'Automated multi-platform ingestion from Instagram, TikTok, YouTube Shorts, X, and Google Trends. Deterministic multi-signal scoring and real-time handoff to Sarah Agent & Social Media Agent.')}
          </p>

          <div className="flex items-center gap-3 mt-6 flex-wrap">
            <Button
              variant="primary"
              onClick={onTriggerRun}
              leftIcon={<PlayCircle className="w-4 h-4 text-[#8b5cf6]" />}
            >
              {t('hero.start_run', 'Start Discovery Run')}
            </Button>
            <Button
              variant="light"
              onClick={() => navigate('/trends')}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              {t('hero.explore', 'Explore Trends')}
            </Button>
          </div>
        </div>
      </div>

      {/* Product workspaces */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6 bg-[#ffffff] hover:border-[#0f172a] transition-colors cursor-pointer" onClick={() => navigate('/trends')}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="w-10 h-10 rounded-xl bg-[#f8fafc] flex items-center justify-center mb-4">
                <Flame className="w-5 h-5 text-[#8b5cf6]" />
              </div>
              <h3 className="text-lg font-bold text-[#0f172a]">{t('ws.prompt_trends.title', 'Prompt Trends')}</h3>
              <p className="text-xs text-[#64748b] mt-1 leading-relaxed">
                {t('ws.prompt_trends.desc', 'Discover, score, and approve reusable trend concepts and AI prompt packages.')}
              </p>
            </div>
            <ArrowRight className="w-4 h-4 text-[#94a3b8]" />
          </div>
        </Card>
        <Card className="p-6 !bg-[#0f172a] !text-[#ffffff] hover:!bg-[#1e293b] transition-colors cursor-pointer" onClick={() => navigate('/social')}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="w-10 h-10 rounded-xl bg-[#1e293b] flex items-center justify-center mb-4">
                <Sparkles className="w-5 h-5 text-[#8b5cf6]" />
              </div>
              <h3 className="text-lg font-bold !text-[#ffffff]">{t('ws.social_agent.title', 'Social Media AI Agent')}</h3>
              <p className="text-xs !text-[#cbd5e1] mt-1 leading-relaxed">
                {t('ws.social_agent.desc', 'Turn briefs and approved trends into platform-ready content, schedules, and publish jobs.')}
              </p>
            </div>
            <ArrowRight className="w-4 h-4 text-[#8b5cf6]" />
          </div>
        </Card>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('stat.total_trends', 'Total Trends Discovered')}
          value={totalTrendsCount || trends.length || '0'}
          icon={<Flame className="w-5 h-5 text-[#8b5cf6]" />}
          color="paper"
          subtitle={t('stat.total_trends.sub', 'Saved in database')}
        />
        <StatCard
          title={t('stat.approved', 'Approved Trends')}
          value={approvedCount || '0'}
          icon={<CheckCircle className="w-5 h-5 text-emerald-600" />}
          color="lime"
          subtitle={t('stat.approved.sub', 'Dispatched to Sarah Agent')}
        />
        <StatCard
          title={t('stat.pending', 'Pending Reviews')}
          value={pendingCount || '0'}
          icon={<Clock className="w-5 h-5 text-amber-600" />}
          color="orange"
          subtitle={t('stat.pending.sub', 'Awaiting human audit')}
        />
        <StatCard
          title={t('stat.active_runs', 'Active Discovery Runs')}
          value={runs.filter((r) => r.status === 'running' || r.status === 'queued').length || '0'}
          icon={<Activity className="w-5 h-5 text-indigo-600" />}
          color="cyan"
          subtitle={t('stat.active_runs.sub', 'Celery worker running')}
        />
      </div>

      {/* Main Grid: Trends Feed & Discovery Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Trends Feed (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-[#0f172a] tracking-tight">{t('sec.top_trends', 'High-Scoring Concepts')}</h3>
              <p className="text-xs text-[#64748b]">{t('sec.top_trends.sub', 'Top viral concepts ready for review and prompt inspection')}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/trends')} rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
              {t('sec.view_all', 'View All')}
            </Button>
          </div>

          {trends.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {trends.slice(0, 4).map((trend) => (
                <TrendCard
                  key={trend.id}
                  trend={trend}
                  onViewDetail={setSelectedTrend}
                  onReview={setReviewTrend}
                />
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center bg-[#ffffff]">
              <Flame className="w-8 h-8 text-[#94a3b8] mx-auto mb-2" />
              <p className="text-sm font-semibold text-[#0f172a]">{t('sec.no_trends', 'No trends discovered yet')}</p>
              <p className="text-xs text-[#64748b] mt-1 max-w-sm mx-auto">
                {t('sec.no_trends.desc', 'Click below to launch an automated multi-source scraping and analysis task.')}
              </p>
              <Button variant="primary" size="sm" className="mt-4" onClick={onTriggerRun}>
                {t('hero.start_run', 'Launch First Discovery Run')}
              </Button>
            </Card>
          )}
        </div>

        {/* Recent Discovery Runs (1 col) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-[#0f172a] tracking-tight">{t('sec.queue', 'Discovery Queue')}</h3>
              <p className="text-xs text-[#64748b]">{t('sec.queue.sub', 'Celery background jobs')}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/runs')}>
              {t('sec.history', 'History')}
            </Button>
          </div>

          <Card className="space-y-3 p-4 bg-[#ffffff]">
            {runs.length > 0 ? (
              runs.map((run) => (
                <div
                  key={run.id}
                  className="p-3 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] flex items-center justify-between gap-3 hover:border-[#8b5cf6] transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#0f172a] font-mono shrink-0">
                        #{run.id.substring(0, 6)}
                      </span>
                      <TrendRunStatusBadge status={run.status} />
                    </div>
                    <p className="text-[11px] text-[#64748b] mt-1 font-medium truncate max-w-[210px]" title={run.sources?.join(', ')}>
                      {run.sources && run.sources.length > 0
                        ? `${run.sources.length} sources (${run.sources.slice(0, 2).map((s) => s.replace(/_/g, ' ')).join(', ')}${run.sources.length > 2 ? '...' : ''})`
                        : 'All Sources'} • {run.candidate_count} items
                    </p>
                  </div>
                  <span className="text-[10px] text-[#94a3b8] whitespace-nowrap shrink-0 font-mono">
                    {new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-[#94a3b8] text-center py-6">{t('sec.no_runs', 'No recent discovery jobs')}</p>
            )}
          </Card>
        </div>
      </div>

      {/* Modals */}
      <TrendDetailModal
        trendItem={selectedTrend}
        isOpen={!!selectedTrend}
        onClose={() => setSelectedTrend(null)}
        onReview={setReviewTrend}
      />

      <ReviewActionModal
        trend={reviewTrend}
        isOpen={!!reviewTrend}
        onClose={() => setReviewTrend(null)}
        onSuccess={loadData}
      />
    </div>
  );
};
