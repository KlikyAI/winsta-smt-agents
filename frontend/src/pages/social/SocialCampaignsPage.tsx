import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Check, DollarSign, Megaphone, RefreshCw, Send, ShieldCheck, X } from 'lucide-react';
import { socialMediaApi } from '../../api/socialMedia';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { useToast } from '../../context/ToastContext';
import type { CreateSocialCampaignRequest, SocialBrief, SocialCampaign, SocialPlatform } from '../../types/socialMedia';

const platforms: Array<{ id: SocialPlatform; label: string }> = [
  { id: 'facebook', label: 'Facebook' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'tiktok', label: 'TikTok' },
  { id: 'youtube', label: 'YouTube' },
  { id: 'linkedin', label: 'LinkedIn' },
  { id: 'x', label: 'X' },
  { id: 'threads', label: 'Threads' },
];

const statusLabel: Record<string, string> = {
  draft: 'Draft',
  pending_approval: 'Pending approval',
  approved: 'Approved',
  rejected: 'Rejected',
  active: 'Active',
  paused: 'Paused',
  completed: 'Completed',
};

const statusClass: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-600',
  pending_approval: 'bg-amber-100 text-amber-700',
  approved: 'bg-violet-100 text-violet-700',
  rejected: 'bg-rose-100 text-rose-700',
  active: 'bg-lime-100 text-lime-700',
  paused: 'bg-slate-100 text-slate-600',
  completed: 'bg-sky-100 text-sky-700',
};

const formatBudget = (campaign: SocialCampaign) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: campaign.currency }).format(campaign.budget_cents / 100);

export const SocialCampaignsPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<SocialCampaign[]>([]);
  const [briefs, setBriefs] = useState<SocialBrief[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [objective, setObjective] = useState('Conversions');
  const [budget, setBudget] = useState('');
  const [budgetType, setBudgetType] = useState<'daily' | 'lifetime'>('daily');
  const [audience, setAudience] = useState('');
  const [briefId, setBriefId] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<SocialPlatform[]>(['facebook', 'instagram']);
  const { addToast } = useToast();

  const loadCampaigns = useCallback(async () => {
    setIsLoading(true);
    try {
      const [campaignResponse, briefResponse] = await Promise.allSettled([
        socialMediaApi.getCampaigns(),
        socialMediaApi.getBriefs(1, 100),
      ]);
      if (campaignResponse.status === 'rejected') throw campaignResponse.reason;
      setCampaigns(campaignResponse.value.data?.items || []);
      if (briefResponse.status === 'fulfilled') setBriefs(briefResponse.value.data?.items || []);
    } catch (error) {
      addToast('error', 'Unable to load campaigns', error instanceof Error ? error.message : undefined);
    } finally {
      setIsLoading(false);
    }
  }, [addToast]);

  useEffect(() => { loadCampaigns(); }, [loadCampaigns]);

  const togglePlatform = (platform: SocialPlatform) => {
    setSelectedPlatforms((current) => current.includes(platform)
      ? current.filter((item) => item !== platform)
      : [...current, platform]);
  };

  const createCampaign = async (event: React.FormEvent) => {
    event.preventDefault();
    const amount = Number(budget);
    if (!name.trim() || !Number.isFinite(amount) || amount < 0 || selectedPlatforms.length === 0) {
      addToast('error', 'Complete the campaign name, budget, and at least one platform.');
      return;
    }
    setIsSaving(true);
    const payload: CreateSocialCampaignRequest = {
      name: name.trim(),
      objective: objective.trim() || 'Conversions',
      platforms: selectedPlatforms,
      budget_cents: Math.round(amount * 100),
      budget_type: budgetType,
      currency: 'USD',
      audience: audience.trim() ? { description: audience.trim() } : {},
      brief_id: briefId || undefined,
    };
    try {
      const response = await socialMediaApi.createCampaign(payload);
      setCampaigns((current) => [response.data, ...current]);
      setName('');
      setBudget('');
      setAudience('');
      setBriefId('');
      addToast('success', 'Campaign draft created', 'Submit it for budget approval when the plan is ready.');
    } catch (error) {
      addToast('error', 'Unable to create campaign', error instanceof Error ? error.message : undefined);
    } finally {
      setIsSaving(false);
    }
  };

  const transition = async (campaign: SocialCampaign, action: 'submit' | 'approve' | 'reject') => {
    setActiveId(campaign.id);
    try {
      const response = action === 'submit'
        ? await socialMediaApi.submitCampaign(campaign.id)
        : action === 'approve'
          ? await socialMediaApi.approveCampaign(campaign.id)
          : await socialMediaApi.rejectCampaign(campaign.id, 'Rejected from campaign workspace');
      setCampaigns((current) => current.map((item) => item.id === campaign.id ? response.data : item));
      addToast(action === 'approve' ? 'success' : 'info', action === 'submit' ? 'Campaign submitted' : action === 'approve' ? 'Budget approved' : 'Campaign rejected');
    } catch (error) {
      addToast('error', 'Unable to update campaign', error instanceof Error ? error.message : undefined);
    } finally {
      setActiveId(null);
    }
  };

  const summary = useMemo(() => ({
    total: campaigns.length,
    pending: campaigns.filter((campaign) => campaign.status === 'pending_approval').length,
    approvedBudget: campaigns.filter((campaign) => ['approved', 'active'].includes(campaign.status)).reduce((sum, campaign) => sum + campaign.budget_cents, 0),
  }), [campaigns]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0f172a] p-8 text-white">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#1e293b] px-3 py-1 text-xs font-semibold"><DollarSign className="h-3.5 w-3.5 text-amber-300" /> Paid Social</div>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div><h2 className="text-3xl font-bold tracking-tight">Campaigns</h2><p className="mt-2 max-w-2xl text-sm text-slate-300">Plan paid distribution around approved creatives. Budget-changing actions stay behind an explicit approval gate.</p></div>
          <Button variant="light" size="sm" onClick={loadCampaigns} leftIcon={<RefreshCw className="h-4 w-4" />}>Refresh</Button>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3"><ShieldCheck className="h-4 w-4 shrink-0 text-amber-600" /><p className="text-xs text-amber-900"><strong>Approval required.</strong> This MVP plans and approves campaigns; provider launch APIs are intentionally not called yet.</p></div>

      <div className="grid gap-4 md:grid-cols-3">
        {[['Campaigns', summary.total], ['Pending approval', summary.pending], ['Approved budget', new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(summary.approvedBudget / 100)]].map(([label, value]) => <Card key={String(label)} className="bg-white p-5"><p className="text-xs font-black uppercase tracking-wider text-slate-400">{label}</p><p className="mt-2 text-2xl font-black text-slate-900">{value}</p></Card>)}
      </div>

      <Card className="bg-white p-6">
        <div className="mb-5 flex items-center gap-2"><Megaphone className="h-4 w-4 text-violet-600" /><div><h3 className="text-sm font-black text-slate-900">Campaign planner</h3><p className="text-xs text-slate-500">Create a draft, then submit it for approval.</p></div></div>
        <form onSubmit={createCampaign} className="grid gap-4 md:grid-cols-2">
          <label className="text-xs font-bold text-slate-600">Campaign name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ramadan launch" className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-normal outline-none focus:border-slate-900" /></label>
          <label className="text-xs font-bold text-slate-600">Objective<input value={objective} onChange={(event) => setObjective(event.target.value)} placeholder="Conversions" className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-normal outline-none focus:border-slate-900" /></label>
          <label className="text-xs font-bold text-slate-600">Budget (USD)<input value={budget} onChange={(event) => setBudget(event.target.value)} type="number" min="0" step="0.01" placeholder="250" className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-normal outline-none focus:border-slate-900" /></label>
          <label className="text-xs font-bold text-slate-600">Budget cadence<select value={budgetType} onChange={(event) => setBudgetType(event.target.value as 'daily' | 'lifetime')} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal outline-none focus:border-slate-900"><option value="daily">Daily</option><option value="lifetime">Lifetime</option></select></label>
          <label className="text-xs font-bold text-slate-600 md:col-span-2">Audience description (optional)<textarea value={audience} onChange={(event) => setAudience(event.target.value)} rows={2} placeholder="Indonesian beauty and skincare shoppers, age 18–34" className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-normal outline-none focus:border-slate-900" /></label>
          <label className="text-xs font-bold text-slate-600 md:col-span-2">Source content brief (optional)<select value={briefId} onChange={(event) => setBriefId(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-normal outline-none focus:border-slate-900"><option value="">No brief linked</option>{briefs.map((brief) => <option key={brief.id} value={brief.id}>{brief.title} · {brief.status}</option>)}</select><span className="mt-1 block text-[10px] font-normal text-slate-400">Link the content brief that supplies the campaign creative.</span></label>
          <div className="md:col-span-2"><p className="mb-2 text-xs font-bold text-slate-600">Platforms</p><div className="flex flex-wrap gap-2">{platforms.map((platform) => <button key={platform.id} type="button" onClick={() => togglePlatform(platform.id)} className={`rounded-full border px-3 py-2 text-xs font-bold ${selectedPlatforms.includes(platform.id) ? 'border-violet-600 bg-violet-50 text-violet-700' : 'border-slate-200 text-slate-500'}`}>{platform.label}</button>)}</div></div>
          <div className="md:col-span-2"><Button type="submit" variant="primary" isLoading={isSaving} leftIcon={<Megaphone className="h-4 w-4" />}>Create campaign draft</Button></div>
        </form>
      </Card>

      {isLoading ? <Card className="bg-white p-10 text-center text-sm text-slate-500">Loading campaigns…</Card> : campaigns.length === 0 ? <Card className="bg-white p-10 text-center"><Megaphone className="mx-auto mb-3 h-8 w-8 text-slate-300" /><p className="font-bold text-slate-900">No campaign drafts yet</p><p className="mt-1 text-xs text-slate-500">Create a campaign plan above after preparing your content creative.</p></Card> : <div className="space-y-3">{campaigns.map((campaign) => <Card key={campaign.id} className="bg-white p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="flex flex-wrap items-center gap-2"><h3 className="font-bold text-slate-900">{campaign.name}</h3><span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase ${statusClass[campaign.status] || statusClass.draft}`}>{statusLabel[campaign.status] || campaign.status}</span></div><p className="mt-1 text-xs text-slate-500">{campaign.objective} · {campaign.platforms.map((platform) => platform === 'x' ? 'X' : platform.charAt(0).toUpperCase() + platform.slice(1)).join(', ')}</p></div><div className="text-right"><p className="text-lg font-black text-slate-900">{formatBudget(campaign)}</p><p className="text-[10px] uppercase text-slate-400">{campaign.budget_type} budget</p></div></div><div className="mt-4 flex flex-wrap gap-2">{campaign.status === 'draft' || campaign.status === 'rejected' ? <Button variant="secondary" size="sm" disabled={activeId === campaign.id} onClick={() => transition(campaign, 'submit')} leftIcon={<Send className="h-3.5 w-3.5" />}>Submit for approval</Button> : null}{campaign.status === 'pending_approval' ? <><Button variant="danger" size="sm" disabled={activeId === campaign.id} onClick={() => transition(campaign, 'reject')} leftIcon={<X className="h-3.5 w-3.5" />}>Reject</Button><Button variant="lime" size="sm" isLoading={activeId === campaign.id} onClick={() => transition(campaign, 'approve')} leftIcon={<Check className="h-3.5 w-3.5" />}>Approve budget</Button></> : null}</div></Card>)}</div>}
    </div>
  );
};
