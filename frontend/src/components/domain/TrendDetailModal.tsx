import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  BarChart2,
  Share2,
  History,
  CheckCircle,
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Tabs } from '../common/Tabs';
import { Button } from '../common/Button';
import { TrendStatusBadge } from '../common/Badge';
import { ScoreMeter } from '../common/ScoreMeter';
import { PromptPackageViewer } from './PromptPackageViewer';
import type { TrendDetail, TrendListItem } from '../../types/trend';
import type { PromptPackage } from '../../types/promptPackage';
import { trendsApi } from '../../api/trends';
import { promptPackagesApi } from '../../api/promptPackages';
import { useToast } from '../../context/ToastContext';
import { useLanguage } from '../../context/LanguageContext';

interface TrendDetailModalProps {
  trendItem: TrendListItem | null;
  isOpen: boolean;
  onClose: () => void;
  onReview?: (trend: TrendListItem) => void;
}

export const TrendDetailModal: React.FC<TrendDetailModalProps> = ({
  trendItem,
  isOpen,
  onClose,
  onReview,
}) => {
  const { addToast } = useToast();
  const { t } = useLanguage();
  const [detail, setDetail] = useState<TrendDetail | null>(null);
  const [latestPrompt, setLatestPrompt] = useState<PromptPackage | null>(null);
  const [allPrompts, setAllPrompts] = useState<PromptPackage[]>([]);
  const [activeTab, setActiveTab] = useState('prompts');
  const [isRegenerating, setIsRegenerating] = useState(false);

  useEffect(() => {
    if (isOpen && trendItem) {
      loadDetail(trendItem.id);
    }
  }, [isOpen, trendItem]);

  const loadDetail = async (id: string) => {
    try {
      const res = await trendsApi.getTrendDetail(id);
      setDetail(res.data);

      try {
        const [latestRes, allRes] = await Promise.all([
          promptPackagesApi.getLatest(id),
          promptPackagesApi.getPackages(id),
        ]);
        setLatestPrompt(latestRes.data);
        setAllPrompts(allRes.data || []);
      } catch {
        setLatestPrompt(null);
        setAllPrompts([]);
      }
    } catch (err: any) {
      addToast('error', 'Failed to load details', err.message);
    }
  };

  const handleRegenerate = async () => {
    if (!trendItem) return;
    setIsRegenerating(true);
    try {
      await promptPackagesApi.regenerate(trendItem.id);
      addToast(
        'info',
        'Generating New Prompts',
        'AI engine is synthesizing fresh text-to-image and video motion prompt variations.'
      );
      setTimeout(async () => {
        await loadDetail(trendItem.id);
        setIsRegenerating(false);
        addToast('success', 'Prompts Updated', 'New prompt package variation is ready to review and copy.');
      }, 2500);
    } catch (err: any) {
      addToast('error', 'Regeneration Failed', err.message);
      setIsRegenerating(false);
    }
  };

  if (!trendItem) return null;

  const tabs = [
    { id: 'prompts', label: t('modal.detail.tab_prompts', 'AI Prompts Studio'), icon: <Sparkles className="w-4 h-4" /> },
    { id: 'signals', label: t('modal.detail.tab_signals', 'Scoring Signals'), icon: <BarChart2 className="w-4 h-4" />, badge: detail?.signals.length },
    { id: 'evidence', label: t('modal.detail.tab_evidence', 'Evidence Sources'), icon: <Share2 className="w-4 h-4" />, badge: detail?.evidence.length },
    { id: 'reviews', label: t('modal.detail.tab_reviews', 'Audit History'), icon: <History className="w-4 h-4" />, badge: detail?.reviews.length },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={detail?.title || trendItem.title}
      description={`${t('modal.detail.category', 'Category')}: ${detail?.category ? detail.category.replace('_', ' ') : 'General'} • ${t('modal.detail.discovered', 'Discovered')} ${new Date(
        trendItem.created_at
      ).toLocaleDateString()}`}
      maxWidth="4xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <TrendStatusBadge status={detail?.status || trendItem.status} />
            {detail?.risk_level && (
              <span className="text-xs text-[#64748b]">
                {t('modal.detail.risk', 'Risk Level')}: <strong className="text-[#0f172a] capitalize">{detail.risk_level}</strong>
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {detail?.status === 'pending_review' && onReview && (
              <Button
                variant="lime"
                size="sm"
                onClick={() => {
                  onClose();
                  onReview(detail);
                }}
                leftIcon={<CheckCircle className="w-4 h-4" />}
              >
                {t('modal.detail.review_btn', 'Review & Approve')}
              </Button>
            )}
            <Button variant="light" size="sm" onClick={onClose}>
              {t('modal.detail.close_btn', 'Close')}
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Core Concept Banner */}
        {detail?.core_concept && (
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-sm text-[#0f172a]">
            <span className="clova-eyebrow text-[#0f172a] block mb-1">
              {t('modal.detail.core_concept', 'Core Concept Summary')}
            </span>
            <p className="leading-relaxed font-medium">{detail.core_concept}</p>
          </div>
        )}

        {/* Tab Navigation */}
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {/* Tab Contents */}
        {activeTab === 'prompts' && (
          <PromptPackageViewer
            packageData={latestPrompt}
            allPackages={allPrompts}
            onSelectVersion={(pkg) => setLatestPrompt(pkg)}
            onRegenerate={handleRegenerate}
            isRegenerating={isRegenerating}
          />
        )}

        {activeTab === 'signals' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 rounded-2xl bg-slate-50 border border-slate-200">
              <span className="text-sm font-bold text-[#0f172a]">Overall Weighted Score:</span>
              <ScoreMeter score={detail?.overall_score} size="md" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {detail?.signals.map((sig, idx) => (
                <div key={idx} className="p-4 rounded-2xl bg-[#ffffff] border border-slate-200 shadow-xs flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] block">
                      {sig.signal_type.replace('_', ' ')}
                    </span>
                    <span className="text-[11px] text-[#64748b]">
                      Raw: {sig.raw_value} • Weight: {sig.weight}%
                    </span>
                  </div>
                  <span className="text-base font-bold text-[#0f172a]">{sig.weighted_score.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="space-y-2">
            {detail?.evidence && detail.evidence.length > 0 ? (
              detail.evidence.map((ev, idx) => (
                <div key={idx} className="p-3.5 rounded-2xl bg-[#ffffff] border border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-extrabold uppercase px-3 py-1 rounded-full bg-purple-50 text-[#8b5cf6] border border-purple-200">
                      {ev.platform}
                    </span>
                    <span className="text-xs text-[#64748b]">Candidate: <code className="text-[#0f172a] font-bold" dir="ltr">{ev.trend_candidate_id.substring(0, 8)}...</code></span>
                  </div>
                  <span className="text-xs font-medium text-[#64748b]">{new Date(ev.created_at).toLocaleDateString()}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-[#64748b] text-center py-6">No evidence linked yet</p>
            )}
          </div>
        )}

        {activeTab === 'reviews' && (
          <div className="space-y-3">
            {detail?.reviews && detail.reviews.length > 0 ? (
              detail.reviews.map((rev, idx) => (
                <div key={idx} className="p-4 rounded-2xl bg-[#ffffff] border border-slate-200">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold uppercase px-2.5 py-0.5 rounded-full border ${
                        rev.decision === 'approve'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : rev.decision === 'reject'
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : 'bg-purple-50 text-purple-700 border-purple-200'
                      }`}>
                        {rev.decision}
                      </span>
                      <span className="text-xs font-bold text-[#0f172a]">by {rev.reviewer_name || 'Reviewer'}</span>
                    </div>
                    <span className="text-[11px] text-[#64748b]">{new Date(rev.created_at).toLocaleString()}</span>
                  </div>
                  {rev.notes && <p className="text-xs text-[#64748b] mt-1">{rev.notes}</p>}
                </div>
              ))
            ) : (
              <p className="text-xs text-[#64748b] text-center py-6">No reviews recorded yet</p>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};
