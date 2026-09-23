import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CalendarDays, Clock3, RefreshCw, Send, ShieldCheck } from 'lucide-react';
import { socialMediaApi } from '../../api/socialMedia';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { useToast } from '../../context/ToastContext';
import type { SocialContentQueueItem, SocialPublishJob } from '../../types/socialMedia';

const defaultSchedule = () => {
  const date = new Date(Date.now() + 60 * 60 * 1000);
  date.setMinutes(Math.ceil(date.getMinutes() / 15) * 15, 0, 0);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
};

const statusClass = (status: string) => {
  if (status === 'published') return 'bg-[#8b5cf6] text-[#0f172a]';
  if (status === 'connection_required' || status === 'failed') return 'bg-[#ffddd1] text-[#a3330d]';
  return 'bg-[#f1f5f9] text-[#64748b]';
};

export const SocialCalendarPage: React.FC = () => {
  const [approved, setApproved] = useState<SocialContentQueueItem[]>([]);
  const [jobs, setJobs] = useState<SocialPublishJob[]>([]);
  const [scheduleValues, setScheduleValues] = useState<Record<string, string>>({});
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { addToast } = useToast();
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

  const loadData = useCallback(async (quiet = false) => {
    if (!quiet) setIsLoading(true);
    try {
      const [contentResponse, jobsResponse] = await Promise.all([
        socialMediaApi.getContent('approved'),
        socialMediaApi.getPublishJobs(),
      ]);
      const contentItems = contentResponse.data?.items || [];
      setApproved(contentItems);
      setJobs(jobsResponse.data?.items || []);
      setScheduleValues((current) => {
        const next = { ...current };
        contentItems.forEach((item) => { if (!next[item.id]) next[item.id] = defaultSchedule(); });
        return next;
      });
    } catch (error) {
      if (!quiet) addToast('error', 'Unable to load the calendar', error instanceof Error ? error.message : undefined);
    } finally {
      if (!quiet) setIsLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadData();
    const poller = window.setInterval(() => loadData(true), 5000);
    return () => window.clearInterval(poller);
  }, [loadData]);

  const schedule = async (item: SocialContentQueueItem, publishNow = false) => {
    setActiveId(item.id);
    try {
      const localValue = scheduleValues[item.id];
      await socialMediaApi.scheduleContent(item.id, {
        scheduled_at: publishNow || !localValue ? undefined : new Date(localValue).toISOString(),
        timezone,
      });
      addToast('success', publishNow ? 'Publish job created' : 'Content scheduled', publishNow ? 'The worker will verify the platform connection.' : 'All variants were added to the publishing queue.');
      await loadData(true);
    } catch (error) {
      addToast('error', 'Unable to schedule the content', error instanceof Error ? error.message : undefined);
    } finally {
      setActiveId(null);
    }
  };

  const operateJob = async (job: SocialPublishJob, action: 'retry' | 'cancel') => {
    setActiveId(job.id);
    try {
      if (action === 'retry') await socialMediaApi.retryPublishJob(job.id);
      else await socialMediaApi.cancelPublishJob(job.id);
      addToast('success', action === 'retry' ? 'Publish job queued again' : 'Publish job cancelled');
      await loadData(true);
    } catch (error) {
      addToast('error', `Unable to ${action} the job`, error instanceof Error ? error.message : undefined);
    } finally {
      setActiveId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0f172a] p-8 text-[#ffffff]">
        <div className="inline-flex items-center gap-2 rounded-full bg-[#1e293b] px-3 py-1 text-xs font-semibold"><CalendarDays className="h-3.5 w-3.5 text-[#8b5cf6]" /> Publishing Operations</div>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Calendar & Publishing</h2>
            <p className="mt-2 max-w-2xl text-sm text-[#cbd5e1]">Schedule approved content and monitor delivery status for every platform.</p>
          </div>
          <Button variant="light" size="sm" onClick={() => loadData()} leftIcon={<RefreshCw className="h-4 w-4" />}>Refresh</Button>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-2xl border border-[#e2e8f0] bg-[#f1f5f9] px-4 py-3">
        <ShieldCheck className="h-4 w-4 shrink-0 text-[#8b5cf6]" />
        <p className="text-xs text-[#64748b]"><strong className="text-[#0f172a]">Safe publishing is active.</strong> Jobs pause as connection required until an authorized account and publisher adapter are available.</p>
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <div><h3 className="text-lg font-bold">Ready to schedule</h3><p className="text-xs text-[#64748b]">Content that has passed human approval</p></div>
          <span className="rounded-full bg-[#0f172a] px-3 py-1 text-xs font-bold text-white">{approved.length}</span>
        </div>
        {isLoading ? (
          <Card className="bg-white p-8 text-center text-sm text-[#64748b]">Loading the publishing workspace…</Card>
        ) : approved.length === 0 ? (
          <Card className="bg-white p-8 text-center"><Clock3 className="mx-auto mb-2 h-7 w-7 text-[#94a3b8]" /><p className="font-bold">No content is ready to schedule</p><p className="mt-1 text-xs text-[#64748b]">Approve content from Social Approvals first.</p></Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {approved.map((item) => (
              <Card key={item.id} className="bg-white p-5">
                <p className="text-[10px] font-black uppercase tracking-widest text-[#8b5cf6]">Approved</p>
                <h4 className="mt-1 font-bold">{item.brief_title}</h4>
                <p className="mt-1 text-xs text-[#64748b]">{item.variants.map((variant) => variant.platform).join(' • ')}</p>
                <label className="mt-4 block text-xs font-bold text-[#64748b]">Publish date & time
                  <input type="datetime-local" value={scheduleValues[item.id] || ''} onChange={(event) => setScheduleValues((current) => ({ ...current, [item.id]: event.target.value }))} className="mt-2 w-full rounded-xl border border-[#e2e8f0] px-3 py-2.5 text-sm font-normal outline-none focus:border-[#0f172a]" />
                </label>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="lime" size="sm" isLoading={activeId === item.id} onClick={() => schedule(item)} leftIcon={<CalendarDays className="h-4 w-4" />}>Schedule</Button>
                  <Button variant="secondary" size="sm" disabled={activeId === item.id} onClick={() => schedule(item, true)} leftIcon={<Send className="h-4 w-4" />}>Publish now</Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="mb-3"><h3 className="text-lg font-bold">Publishing queue</h3><p className="text-xs text-[#64748b]">Job history, schedules, and delivery status</p></div>
        {jobs.length === 0 ? (
          <Card className="bg-white p-8 text-center text-sm text-[#64748b]">Publishing queue masih kosong.</Card>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <Card key={job.id} className="bg-white p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2"><span className="font-bold capitalize">{job.platform === 'x' ? 'X' : job.platform}</span><span className={`rounded-full px-2 py-1 text-[9px] font-black uppercase ${statusClass(job.status)}`}>{job.status.replaceAll('_', ' ')}</span></div>
                    <p className="mt-1 text-sm font-semibold">{job.brief_title}</p>
                    <p className="mt-1 text-xs text-[#64748b]">{job.scheduled_at ? new Date(job.scheduled_at).toLocaleString('id-ID') : 'Publish immediately'} • {job.timezone || 'UTC'} • attempt {job.attempt_count}/{job.max_attempts}</p>
                    <div className="mt-3 flex gap-2">
                      {(['failed', 'connection_required', 'media_required', 'cancelled'].includes(job.status) || (job.status === 'scheduled' && Boolean(job.error))) && <Button variant="secondary" size="sm" isLoading={activeId === job.id} onClick={() => operateJob(job, 'retry')}>{job.status === 'failed' || (job.status === 'scheduled' && Boolean(job.error)) ? 'Publish again' : 'Retry'}</Button>}
                      {['queued', 'scheduled', 'failed', 'connection_required', 'media_required'].includes(job.status) && <Button variant="ghost" size="sm" disabled={activeId === job.id} onClick={() => operateJob(job, 'cancel')}>Cancel</Button>}
                    </div>
                  </div>
                  {job.error && <div className="flex max-w-md items-start gap-2 rounded-xl bg-[#fff2ed] px-3 py-2 text-xs text-[#a3330d]"><AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{job.error}</div>}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
