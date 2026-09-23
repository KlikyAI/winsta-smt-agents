import React, { useState } from 'react';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import type { TrendListItem } from '../../types/trend';
import type { ReviewDecision } from '../../types/review';
import { approvalsApi } from '../../api/approvals';
import { useToast } from '../../context/ToastContext';
import { useLanguage } from '../../context/LanguageContext';

interface ReviewActionModalProps {
  trend: TrendListItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ReviewActionModal: React.FC<ReviewActionModalProps> = ({
  trend,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { addToast } = useToast();
  const { t } = useLanguage();
  const [decision, setDecision] = useState<ReviewDecision>('approve');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!trend) return null;

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await approvalsApi.reviewTrend(trend.id, { decision, notes });
      addToast(
        decision === 'approve' ? 'success' : decision === 'reject' ? 'error' : 'info',
        `Trend ${decision === 'approve' ? 'Approved' : decision === 'reject' ? 'Rejected' : 'Sent for Regeneration'}`,
        decision === 'approve' ? 'Dispatched delivery to Sarah Agent & Social Media Agent' : undefined
      );
      onSuccess();
      onClose();
    } catch (err: any) {
      addToast('error', 'Review Failed', err.message || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t('modal.review.title', 'Audit & Review Decision')}
      description={`${t('modal.review.description', 'Human-in-the-loop review for:')} "${trend.title}"`}
      maxWidth="lg"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
            {t('modal.review.cancel', 'Cancel')}
          </Button>
          <Button
            variant={decision === 'approve' ? 'lime' : decision === 'reject' ? 'danger' : 'primary'}
            onClick={handleSubmit}
            isLoading={isSubmitting}
          >
            {t('modal.review.confirm', 'Confirm')} {decision === 'approve' ? t('modal.review.approve', 'Approval') : decision === 'reject' ? t('modal.review.reject', 'Rejection') : t('modal.review.regenerate', 'Regeneration')}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Decision Selector Cards */}
        <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider">
          {t('modal.review.choice', 'Decision Choice')}
        </label>
        <div className="grid grid-cols-3 gap-3">
          <div
            onClick={() => setDecision('approve')}
            className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${
              decision === 'approve'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-500 shadow-xs font-bold'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <CheckCircle2 className={`w-5 h-5 ${decision === 'approve' ? 'text-emerald-600' : 'text-slate-400'}`} />
            <div>
              <span className="text-xs font-bold block">{t('modal.review.approve', 'Approve')}</span>
              <span className="text-[10px] opacity-75">{t('modal.review.approve_sub', 'Send downstream')}</span>
            </div>
          </div>

          <div
            onClick={() => setDecision('request_regeneration')}
            className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${
              decision === 'request_regeneration'
                ? 'bg-purple-50 text-purple-800 border-[#8b5cf6] shadow-xs font-bold'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <RefreshCw className={`w-5 h-5 ${decision === 'request_regeneration' ? 'text-[#8b5cf6]' : 'text-slate-400'}`} />
            <div>
              <span className="text-xs font-bold block">{t('modal.review.regenerate', 'Regenerate')}</span>
              <span className="text-[10px] opacity-75">{t('modal.review.regenerate_sub', 'Request new')}</span>
            </div>
          </div>

          <div
            onClick={() => setDecision('reject')}
            className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex flex-col items-center text-center gap-2 ${
              decision === 'reject'
                ? 'bg-rose-50 text-rose-800 border-rose-500 shadow-xs font-bold'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <XCircle className={`w-5 h-5 ${decision === 'reject' ? 'text-rose-600' : 'text-slate-400'}`} />
            <div>
              <span className="text-xs font-bold block">{t('modal.review.reject', 'Reject')}</span>
              <span className="text-[10px] opacity-75">{t('modal.review.reject_sub', 'Archive concept')}</span>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1.5">
            {t('modal.review.notes', 'Audit Notes / Reason (Optional)')}
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t('modal.review.notes_placeholder', 'e.g. Concept aligned with upcoming campaign...')}
            rows={3}
            className="w-full bg-white border border-slate-300 focus:border-[#8b5cf6] rounded-2xl p-3.5 text-sm text-slate-900 placeholder-slate-400 outline-none shadow-xs"
          />
        </div>
      </div>
    </Modal>
  );
};
