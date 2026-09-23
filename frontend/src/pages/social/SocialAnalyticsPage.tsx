import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BarChart3, FlaskConical, Lightbulb, RefreshCw, TrendingUp } from 'lucide-react';
import { socialMediaApi } from '../../api/socialMedia';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { PlatformLogo } from '../../components/common/PlatformLogo';
import { useToast } from '../../context/ToastContext';
import type { SocialMetricSnapshot, SocialPerformanceInsight } from '../../types/socialMedia';

const formatMetric = (value: unknown) => {
  if (typeof value === 'number') return value.toLocaleString('en-US');
  if (typeof value === 'object' && value !== null) return JSON.stringify(value);
  return String(value ?? '—');
};

export const SocialAnalyticsPage: React.FC = () => {
  const [snapshots, setSnapshots] = useState<SocialMetricSnapshot[]>([]);
  const [insights, setInsights] = useState<SocialPerformanceInsight[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { addToast } = useToast();

  const loadAnalytics = useCallback(async () => {
    setIsLoading(true);
    try {
      const [analyticsResponse, insightsResponse] = await Promise.all([
        socialMediaApi.getAnalytics(),
        socialMediaApi.getPerformanceInsights(),
      ]);
      setSnapshots(analyticsResponse.data || []);
      setInsights(insightsResponse.data || []);
    } catch (error) {
      addToast('error', 'Unable to load analytics', error instanceof Error ? error.message : undefined);
    } finally {
      setIsLoading(false);
    }
  }, [addToast]);

  useEffect(() => { loadAnalytics(); }, [loadAnalytics]);

  const analyzePerformance = async () => {
    setIsAnalyzing(true);
    try {
      const response = await socialMediaApi.analyzePerformance();
      setInsights(response.data || []);
      addToast('success', 'Optimization refreshed', `${response.data?.length || 0} insight segments generated.`);
    } catch (error) {
      addToast('error', 'Unable to analyze performance', error instanceof Error ? error.message : undefined);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const latest = useMemo(() => snapshots[0], [snapshots]);
  const metricCount = snapshots.reduce((count, snapshot) => count + Object.keys(snapshot.metrics || {}).length, 0);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0f172a] p-8 text-[#ffffff]">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#1e293b] px-3 py-1 text-xs font-semibold"><BarChart3 className="h-3.5 w-3.5 text-[#8b5cf6]" /> Platform Analytics</div>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Social Analytics</h2>
            <p className="mt-2 max-w-2xl text-sm text-[#cbd5e1]">Verified snapshots collected from published Meta posts. The scheduled worker refreshes these metrics every 30 minutes.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="light" size="sm" onClick={analyzePerformance} isLoading={isAnalyzing} leftIcon={<FlaskConical className="h-4 w-4" />}>Analyze</Button>
            <Button variant="light" size="sm" onClick={loadAnalytics} leftIcon={<RefreshCw className="h-4 w-4" />}>Refresh</Button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          ['Snapshots', snapshots.length.toLocaleString('en-US')],
          ['Published posts tracked', new Set(snapshots.map((snapshot) => snapshot.external_post_id)).size.toLocaleString('en-US')],
          ['Metric values', metricCount.toLocaleString('en-US')],
        ].map(([label, value]) => <Card key={label} className="bg-white p-5"><p className="text-xs font-black uppercase tracking-wider text-[#94a3b8]">{label}</p><p className="mt-2 text-3xl font-black">{value}</p></Card>)}
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-[#8b5cf6]" />
          <div><h3 className="text-sm font-black text-slate-900">AI Optimization Insights</h3><p className="text-xs text-slate-500">Evidence-based recommendations. Every proposed experiment still requires approval.</p></div>
        </div>
        {insights.length === 0 ? (
          <Card className="bg-white p-5 text-sm text-slate-500">No optimization baseline yet. Collect at least one published-post snapshot, then select Analyze.</Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {insights.map((insight) => {
              const recommendation = insight.recommendations?.[0];
              return (
                <Card key={insight.id} className="bg-white p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[10px] font-black uppercase tracking-wider text-[#8b5cf6]">
                        {insight.platform ? [insight.platform, insight.language, insight.content_format].filter(Boolean).join(' / ') : 'Overall baseline'}
                      </p>
                      <p className="mt-2 text-sm font-bold text-slate-900">{insight.summary}</p>
                    </div>
                    <div className="rounded-xl bg-[#f5f3ff] px-3 py-2 text-center">
                      <p className="text-[9px] font-black uppercase text-[#8b5cf6]">Score</p>
                      <p className="text-xl font-black text-[#6d28d9]">{insight.performance_score.toFixed(0)}</p>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg bg-slate-50 p-2"><p className="text-[9px] uppercase text-slate-400">Engagement</p><p className="text-sm font-black">{insight.engagement_rate.toFixed(2)}%</p></div>
                    <div className="rounded-lg bg-slate-50 p-2"><p className="text-[9px] uppercase text-slate-400">Samples</p><p className="text-sm font-black">{insight.sample_size}</p></div>
                    <div className="rounded-lg bg-slate-50 p-2"><p className="text-[9px] uppercase text-slate-400">Confidence</p><p className="text-sm font-black">{Math.round(insight.confidence * 100)}%</p></div>
                  </div>
                  {recommendation?.experiment && <div className="mt-4 rounded-xl border border-violet-100 bg-violet-50 p-3"><p className="text-[10px] font-black uppercase text-violet-700">Proposed experiment: {recommendation.experiment.variable}</p><p className="mt-1 text-xs text-violet-900">{recommendation.experiment.hypothesis}</p></div>}
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {isLoading ? <Card className="bg-white p-10 text-center text-sm text-[#64748b]">Loading verified metrics…</Card> : snapshots.length === 0 ? (
        <Card className="bg-white p-10 text-center"><TrendingUp className="mx-auto mb-3 h-8 w-8 text-[#94a3b8]" /><p className="font-bold">No analytics snapshots yet</p><p className="mt-1 text-xs text-[#64748b]">Publish an approved Instagram or Facebook post with a connected Meta account. The analytics worker will collect the first snapshot automatically.</p></Card>
      ) : (
        <Card className="overflow-hidden bg-white p-0">
          <div className="border-b border-[#e2e8f0] p-5"><p className="font-bold">Latest platform snapshots</p><p className="mt-1 text-xs text-[#64748b]">{latest ? `Last captured ${new Date(latest.captured_at).toLocaleString('en-US')}` : ''}</p></div>
          <div className="divide-y divide-[#f1f5f9]">
            {snapshots.map((snapshot) => <div key={snapshot.id} className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3"><PlatformLogo platform={snapshot.platform} size="md" /><div><p className="text-sm font-bold capitalize">{snapshot.platform}</p><p className="font-mono text-[10px] text-[#94a3b8]">{snapshot.external_post_id}</p></div></div>
                <span className="text-[10px] font-semibold text-[#94a3b8]">{new Date(snapshot.captured_at).toLocaleString('en-US')}</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">{Object.entries(snapshot.metrics || {}).map(([key, value]) => <div key={key} className="rounded-xl bg-[#f8fafc] px-3 py-2"><p className="text-[10px] font-black uppercase tracking-wider text-[#94a3b8]">{key.replaceAll('_', ' ')}</p><p className="mt-1 text-sm font-black">{formatMetric(value)}</p></div>)}</div>
            </div>)}
          </div>
        </Card>
      )}
    </div>
  );
};
