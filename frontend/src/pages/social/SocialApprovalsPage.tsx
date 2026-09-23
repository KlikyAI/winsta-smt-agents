import React, { useCallback, useEffect, useState } from 'react';
import { Check, ClipboardCheck, Copy, RefreshCw, Save, ShieldCheck, X } from 'lucide-react';
import { socialMediaApi } from '../../api/socialMedia';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { useToast } from '../../context/ToastContext';
import type { SocialContentQueueItem } from '../../types/socialMedia';

const platformLabel = (platform: string) =>
  platform === 'x' ? 'X' : platform.charAt(0).toUpperCase() + platform.slice(1);

export const SocialApprovalsPage: React.FC = () => {
  const [items, setItems] = useState<SocialContentQueueItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [captionDrafts, setCaptionDrafts] = useState<Record<string, string>>({});
  const { addToast } = useToast();

  const loadItems = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await socialMediaApi.getContent('ready_for_approval');
      setItems(response.data?.items || []);
    } catch (error) {
      addToast('error', 'Unable to load the approval queue', error instanceof Error ? error.message : undefined);
    } finally {
      setIsLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const review = async (item: SocialContentQueueItem, decision: 'approve' | 'reject', variantId?: string) => {
    setActiveId(variantId || item.id);
    try {
      const response = await socialMediaApi.reviewContent(item.id, {
        decision,
        notes: decision === 'approve' ? 'Approved from Social Approvals workspace' : 'Rejected from Social Approvals workspace',
        variant_ids: variantId ? [variantId] : undefined,
      });
      setItems((current) => response.data.status === 'ready_for_approval'
        ? current.map((candidate) => candidate.id === item.id ? { ...item, ...response.data } : candidate)
        : current.filter((candidate) => candidate.id !== item.id));
      addToast(
        decision === 'approve' ? 'success' : 'info',
        decision === 'approve' ? 'Content approved' : 'Content rejected',
        decision === 'approve' ? 'The content is now ready to schedule.' : 'The decision was saved to the audit history.',
      );
    } catch (error) {
      addToast('error', 'Unable to save the review', error instanceof Error ? error.message : undefined);
    } finally {
      setActiveId(null);
    }
  };

  const saveCaption = async (item: SocialContentQueueItem, variantId: string, currentCaption?: string) => {
    const caption = captionDrafts[variantId] ?? currentCaption ?? '';
    setActiveId(variantId);
    try {
      const response = await socialMediaApi.updateVariant(variantId, { caption });
      setItems((current) => current.map((candidate) => candidate.id === item.id ? { ...item, ...response.data } : candidate));
      addToast('success', 'Variant updated', 'QA was rerun and approval is required again.');
    } catch (error) {
      addToast('error', 'Unable to update the variant', error instanceof Error ? error.message : undefined);
    } finally {
      setActiveId(null);
    }
  };

  const copyCaption = async (caption?: string) => {
    if (!caption) return;
    await navigator.clipboard.writeText(caption);
    addToast('success', 'Caption copied');
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0f172a] p-8 text-[#ffffff]">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#1e293b] px-3 py-1 text-xs font-semibold">
          <ClipboardCheck className="h-3.5 w-3.5 text-[#8b5cf6]" /> Human Review
        </div>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Social Approvals</h2>
            <p className="mt-2 max-w-2xl text-sm text-[#cbd5e1]">Review QA results and platform copy before content enters the publishing calendar.</p>
          </div>
          <Button variant="light" size="sm" onClick={loadItems} leftIcon={<RefreshCw className="h-4 w-4" />}>
            Refresh
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-2xl border border-[#e2e8f0] bg-[#f1f5f9] px-4 py-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-[#8b5cf6]" />
        <p className="text-xs text-[#64748b]"><strong className="text-[#0f172a]">Human-in-the-loop is active.</strong> Content cannot be scheduled before it is approved.</p>
      </div>

      {isLoading ? (
        <Card className="bg-white p-10 text-center text-sm text-[#64748b]">Loading the approval queue…</Card>
      ) : items.length === 0 ? (
        <Card className="bg-white p-10 text-center">
          <Check className="mx-auto mb-3 h-8 w-8 text-[#94a3b8]" />
          <p className="font-bold">The approval queue is clear</p>
          <p className="mt-1 text-xs text-[#64748b]">New content appears here after generation and automated QA are complete.</p>
        </Card>
      ) : (
        <div className="space-y-5">
          {items.map((item) => (
            <Card key={item.id} className="bg-white p-0 overflow-hidden">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e2e8f0] p-5">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-[#8b5cf6]">Ready for approval</p>
                  <h3 className="mt-1 text-lg font-bold">{item.brief_title}</h3>
                  <p className="mt-1 text-xs text-[#64748b]">{item.variants.length} platform variant • {item.ai_model || 'structured generator'}</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="danger" size="sm" disabled={activeId === item.id} onClick={() => review(item, 'reject')} leftIcon={<X className="h-4 w-4" />}>Reject</Button>
                  <Button variant="lime" size="sm" isLoading={activeId === item.id} onClick={() => review(item, 'approve')} leftIcon={<Check className="h-4 w-4" />}>Approve</Button>
                </div>
              </div>
              <div className="grid gap-4 p-5 lg:grid-cols-2">
                {item.variants.map((variant) => (
                  <div key={variant.id} className="rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] p-4">
                    {variant.media_ref && <img src={variant.media_ref} alt={variant.visual_prompt || `${variant.platform} creative`} className="mb-3 aspect-video w-full rounded-xl object-cover" loading="lazy" />}
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-[#0f172a] px-2.5 py-1 text-[10px] font-black uppercase text-white">{platformLabel(variant.platform)} · {variant.language}</span>
                        <span className="text-[10px] font-bold text-[#64748b]">{variant.format} • {variant.aspect_ratio}</span>
                      </div>
                      <span className="rounded-full bg-[#8b5cf6] px-2 py-1 text-[9px] font-black uppercase text-[#0f172a]">QA {variant.qa_result?.score ?? 100}</span>
                    </div>
                    <textarea dir={variant.language === 'ar' ? 'rtl' : 'ltr'} value={captionDrafts[variant.id] ?? variant.caption ?? ''} onChange={(event) => setCaptionDrafts((current) => ({ ...current, [variant.id]: event.target.value }))} rows={7} className="w-full rounded-xl border border-[#e2e8f0] bg-white p-3 text-sm leading-relaxed outline-none focus:border-[#0f172a]" />
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button variant="secondary" size="sm" disabled={activeId === variant.id} onClick={() => saveCaption(item, variant.id, variant.caption)} leftIcon={<Save className="h-3.5 w-3.5" />}>Save</Button>
                      <Button variant="danger" size="sm" disabled={activeId === variant.id} onClick={() => review(item, 'reject', variant.id)} leftIcon={<X className="h-3.5 w-3.5" />}>Reject variant</Button>
                      <Button variant="lime" size="sm" isLoading={activeId === variant.id} onClick={() => review(item, 'approve', variant.id)} leftIcon={<Check className="h-3.5 w-3.5" />}>Approve variant</Button>
                      <button type="button" onClick={() => copyCaption(variant.caption)} className="inline-flex items-center gap-1.5 px-2 text-xs font-bold text-[#64748b] hover:text-[#0f172a]"><Copy className="h-3.5 w-3.5" /> Copy</button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
