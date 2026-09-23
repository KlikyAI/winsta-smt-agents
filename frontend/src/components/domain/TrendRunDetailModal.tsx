import React, { useState, useEffect, useMemo } from 'react';
import { CheckCircle2, XCircle, Layers, AlertCircle, AlertTriangle, ExternalLink, Filter, Loader2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { TrendRunStatusBadge } from '../common/Badge';
import { Button } from '../common/Button';
import { PlatformLogo } from '../common/PlatformLogo';
import type { TrendRun, CandidateItem } from '../../types/trendRun';
import { trendRunsApi } from '../../api/trendRuns';

interface TrendRunDetailModalProps {
  run: TrendRun | null;
  isOpen: boolean;
  onClose: () => void;
}

export const TrendRunDetailModal: React.FC<TrendRunDetailModalProps> = ({
  run,
  isOpen,
  onClose,
}) => {
  const [selectedPlatformTab, setSelectedPlatformTab] = useState<string>('all');
  const [detailRun, setDetailRun] = useState<TrendRun | null>(run);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!run || !isOpen) {
      setDetailRun(run);
      return;
    }

    setDetailRun(run);
    setSelectedPlatformTab('all');

    // Fetch full run detail including candidates list
    const fetchFullRun = async () => {
      setIsLoading(true);
      try {
        const res = (await trendRunsApi.getRunById(run.id)) as any;
        const data = res?.data || res;
        if (data && data.id === run.id) {
          setDetailRun(data);
        }
      } catch (err) {
        console.error('Failed to load run candidates:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFullRun();
  }, [run?.id, isOpen]);

  const activeRun = detailRun || run;
  const candidatesList = activeRun?.candidates || [];

  // Group candidates by platform (Hook placed unconditionally before early return)
  const groupedCandidates = useMemo(() => {
    const map: Record<string, CandidateItem[]> = {
      google_trends: [],
      tiktok: [],
      instagram: [],
      youtube: [],
      x: [],
      linkedin: [],
    };

    candidatesList.forEach((c) => {
      let plat = (c.platform || 'other').toLowerCase().trim();
      if (plat === 'twitter') plat = 'x';
      if (plat === 'google') plat = 'google_trends';
      if (!map[plat]) map[plat] = [];
      map[plat].push(c);
    });

    return map;
  }, [candidatesList]);

  const platformList = ['google_trends', 'tiktok', 'instagram', 'youtube', 'x', 'linkedin'];

  // Filter candidates based on active tab (Hook placed unconditionally before early return)
  const displayedCandidates = useMemo(() => {
    if (selectedPlatformTab === 'all') {
      return candidatesList;
    }
    return groupedCandidates[selectedPlatformTab] || [];
  }, [candidatesList, selectedPlatformTab, groupedCandidates]);

  // Safe early return after all hooks have been declared unconditionally
  if (!activeRun || !isOpen) return null;

  const formattedStartedAt = activeRun.started_at
    ? new Date(activeRun.started_at).toLocaleString()
    : 'Not started';

  const platformErrors = activeRun.metadata?.platform_errors || {};
  const hasErrors = Object.keys(platformErrors).length > 0;

  const getPlatformSourceUrl = (item: CandidateItem) => {
    const cleanTitle = (item.title || '').replace(/🔥|Trending in.*|\(.*\)/g, '').trim();
    const query = encodeURIComponent(cleanTitle || 'trend');
    const firstTag = item.hashtags && item.hashtags[0] ? item.hashtags[0].replace('#', '') : cleanTitle.replace(/\s+/g, '');
    const plat = (item.platform || '').toLowerCase().trim();
    const rawUrl = item.canonical_url || '';

    // If canonical URL is a genuine real scraper URL (not a dummy placeholder ID)
    const isDummyUrl =
      rawUrl.includes('1234567890') ||
      rawUrl.includes('987654321') ||
      rawUrl.includes('youtu.be/kuwaiti') ||
      rawUrl.includes('youtu.be/gulf') ||
      rawUrl.includes('instagram.com/p/Cn');

    if (rawUrl.startsWith('http') && !isDummyUrl && !rawUrl.includes('trends.google.com/trends/explore?q=')) {
      return rawUrl;
    }

    const geo = (activeRun?.metadata?.country || activeRun?.market || 'GLOBAL').toUpperCase();

    switch (plat) {
      case 'instagram':
        return `https://www.instagram.com/explore/tags/${encodeURIComponent(firstTag)}/`;
      case 'tiktok':
        return `https://www.tiktok.com/search?q=${query}`;
      case 'youtube':
        return `https://www.youtube.com/results?search_query=${query}`;
      case 'x':
      case 'twitter':
        return `https://x.com/search?q=${query}&src=typed_query&f=live`;
      case 'linkedin':
        return `https://www.linkedin.com/feed/hashtag/?keywords=${encodeURIComponent(firstTag)}`;
      case 'google_trends':
      case 'google':
      default:
        return `https://trends.google.com/trends/explore?geo=${geo}&q=${query}`;
    }
  };

  const renderCandidateCard = (item: CandidateItem) => {
    const sourceLink = getPlatformSourceUrl(item);

    return (
      <div
        key={item.id}
        className="p-4 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs hover:border-[#0f172a] transition-colors"
      >
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <PlatformLogo platform={item.platform} size="sm" />
            <h5 className="text-xs font-bold text-[#0f172a] truncate">
              {item.title || 'Discovered Visual Trend Item'}
            </h5>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {item.engagement_rate && (
              <span className="px-2 py-0.5 rounded-full bg-slate-50 border border-slate-200 text-[10px] font-bold text-slate-900">
                🔥 {item.engagement_rate}% Eng.
              </span>
            )}
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                item.status === 'accepted'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
            >
              {item.status}
            </span>
          </div>
        </div>

        {item.caption && (
          <p className="text-xs text-slate-500 leading-relaxed line-clamp-2 mb-2.5">
            {item.caption}
          </p>
        )}

        <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-900">{item.author_name || 'Creator'}</span>
            {sourceLink && (
              <a
                href={sourceLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-50 hover:bg-purple-100 text-[#8b5cf6] font-bold transition-all cursor-pointer"
                onClick={(e) => e.stopPropagation()}
              >
                <span>Open Source</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          {item.hashtags && item.hashtags.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {item.hashtags.slice(0, 3).map((tag, idx) => (
                <span key={idx} className="text-[#8b5cf6] font-medium">
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Discovery Run #${activeRun.id.slice(0, 8)}`}
      description={`Target: ${(activeRun.metadata?.country || activeRun.market || 'GLOBAL').toUpperCase()} • Category: ${(activeRun.metadata?.category || 'General').replace('_', ' ')} • Started ${formattedStartedAt}`}
      maxWidth="4xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <TrendRunStatusBadge status={activeRun.status} />
            <span className="text-xs text-[#64748b]">
              Started: {formattedStartedAt}
            </span>
          </div>
          <Button variant="light" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Metric Summary Cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3.5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748b] block mb-1">
              Candidates Ingested
            </span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-black text-[#0f172a]">
                {activeRun.candidate_count}
              </span>
              <Layers className="w-5 h-5 text-[#0f172a]" />
            </div>
            <span className="text-[11px] text-[#64748b] mt-1 block">Raw platform posts</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748b] block mb-1">
              Accepted for Scoring
            </span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-black text-[#0f172a]">
                {activeRun.accepted_count}
              </span>
              <CheckCircle2 className="w-5 h-5 text-[#0f172a]" />
            </div>
            <span className="text-[11px] text-[#64748b] mt-1 block">Passed quality threshold</span>
          </div>

          <div className="p-3.5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#64748b] block mb-1">
              Platform Status
            </span>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-black text-[#0f172a]">
                {hasErrors ? Object.keys(platformErrors).length : '0'}
              </span>
              {hasErrors ? (
                <XCircle className="w-5 h-5 text-[#8b5cf6]" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-[#0f172a]" />
              )}
            </div>
            <span className="text-[11px] text-[#64748b] mt-1 block">
              {hasErrors ? 'API warnings recorded' : 'All sources healthy'}
            </span>
          </div>
        </div>

        {/* Platform Error Diagnosis Box if any */}
        {hasErrors && (
          <div className="p-4 rounded-2xl bg-[#fff2ed] border border-[#ffcfbe] space-y-2.5">
            <div className="flex items-center gap-2 text-xs font-bold text-[#e63900]">
              <AlertTriangle className="w-4 h-4" />
              <span>Platform API Diagnostics ({Object.keys(platformErrors).length} Sources Noticed)</span>
            </div>
            <div className="space-y-2">
              {Object.entries(platformErrors).map(([plat, err]) => (
                <div key={plat} className="p-2.5 rounded-xl bg-white border border-[#ffcfbe] text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-[#0f172a] mb-1">
                    <PlatformLogo platform={plat} size="sm" />
                    <span className="capitalize">{plat.replace('_', ' ')}</span>
                  </div>
                  <p className="text-[#64748b] font-mono text-[11px] break-all leading-relaxed">
                    {String(err)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Platform Sources Tabs / Separation */}
        <div>
          <div className="flex items-center justify-between mb-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-[#8b5cf6]" />
              Filter By Platform Provider
            </h4>
            <span className="text-xs text-[#64748b]">
              Total: <strong>{candidatesList.length || activeRun.candidate_count} items</strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            {/* All Platforms Tab */}
            <button
              type="button"
              onClick={() => setSelectedPlatformTab('all')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer border ${
                selectedPlatformTab === 'all'
                  ? 'bg-[#0f172a] text-white border-[#0f172a] shadow-xs'
                  : 'bg-white text-slate-800 border-slate-200 hover:border-slate-400'
              }`}
            >
              <span>🌐 All Providers</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-black ${
                  selectedPlatformTab === 'all'
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {candidatesList.length || activeRun.candidate_count}
              </span>
            </button>

            {/* Individual Platform Tabs */}
            {platformList.map((plat) => {
              const count = groupedCandidates[plat]?.length || 0;
              const isSelected = selectedPlatformTab === plat;

              return (
                <button
                  key={plat}
                  type="button"
                  onClick={() => setSelectedPlatformTab(plat)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer border ${
                    isSelected
                      ? 'bg-[#0f172a] text-white border-[#0f172a] shadow-xs'
                      : 'bg-white text-slate-800 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  <PlatformLogo platform={plat} size="sm" />
                  <span className="capitalize">{plat.replace('_', ' ')}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-black ${
                      isSelected
                        ? 'bg-purple-100 text-purple-700'
                        : count > 0
                        ? 'bg-purple-50 text-purple-700'
                        : 'bg-slate-100 text-slate-400'
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Discovered Candidate Items Feed (Grouped or Filtered) */}
        <div>
          {isLoading ? (
            <div className="p-12 rounded-2xl bg-[#ffffff] border border-slate-200 text-center space-y-2">
              <Loader2 className="w-7 h-7 text-[#8b5cf6] animate-spin mx-auto" />
              <p className="text-xs font-bold text-slate-900">Loading Candidate Items...</p>
              <p className="text-[11px] text-slate-500">Retrieving multi-platform feed records from database</p>
            </div>
          ) : displayedCandidates.length > 0 ? (
            selectedPlatformTab === 'all' ? (
              <div className="space-y-6">
                {platformList.map((plat) => {
                  const items = groupedCandidates[plat] || [];
                  if (items.length === 0) return null;

                  return (
                    <div key={plat} className="space-y-2.5">
                      <div className="flex items-center justify-between pb-1 border-b border-slate-200">
                        <div className="flex items-center gap-2">
                          <PlatformLogo platform={plat} size="sm" />
                          <h5 className="text-xs font-extrabold uppercase tracking-wider text-slate-900">
                            {plat.replace('_', ' ')}
                          </h5>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0f172a] text-[#a78bfa] font-black">
                            {items.length} Items
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-500">
                          Live Ingestion Feed
                        </span>
                      </div>

                      <div className="space-y-3">
                        {items.map(renderCandidateCard)}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-1 border-b border-slate-200">
                  <div className="flex items-center gap-2">
                    <PlatformLogo platform={selectedPlatformTab} size="sm" />
                    <h5 className="text-xs font-extrabold uppercase tracking-wider text-slate-900">
                      {selectedPlatformTab.replace('_', ' ')} Results
                    </h5>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0f172a] text-[#a78bfa] font-black">
                      {displayedCandidates.length} Items
                    </span>
                  </div>
                </div>
                {displayedCandidates.map(renderCandidateCard)}
              </div>
            )
          ) : (
            <div className="p-8 rounded-2xl bg-[#ffffff] border border-dashed border-slate-200 text-center">
              <AlertCircle className="w-8 h-8 text-[#8b5cf6] mx-auto mb-2" />
              <p className="text-xs font-bold text-[#0f172a]">
                {selectedPlatformTab !== 'all' && platformErrors[selectedPlatformTab]
                  ? `${selectedPlatformTab.replace('_', ' ').toUpperCase()} Ingestion Failed / Offline`
                  : 'No Candidates Ingested'}
              </p>
              <p className="text-[11px] text-[#64748b] mt-1 max-w-md mx-auto">
                {selectedPlatformTab !== 'all' && platformErrors[selectedPlatformTab]
                  ? platformErrors[selectedPlatformTab]
                  : hasErrors
                  ? 'Check the Platform API Diagnostics box above for provider failure details.'
                  : 'No candidate items collected for this specific provider in this run.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
};
