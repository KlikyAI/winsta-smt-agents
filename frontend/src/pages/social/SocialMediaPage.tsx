import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CalendarClock, CheckCircle2, Image, Plus, Send, Sparkles, UploadCloud } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { socialMediaApi } from '../../api/socialMedia';
import type { CreateSocialBriefRequest, SocialBrief, SocialLanguage, SocialPlatform } from '../../types/socialMedia';
import { useToast } from '../../context/ToastContext';

const platforms: { id: SocialPlatform; label: string }[] = [
  { id: 'instagram', label: 'Instagram' },
  { id: 'facebook', label: 'Facebook' },
  { id: 'tiktok', label: 'TikTok' },
  { id: 'youtube', label: 'YouTube' },
  { id: 'x', label: 'X' },
  { id: 'linkedin', label: 'LinkedIn' },
  { id: 'threads', label: 'Threads' },
];

const languages: { id: SocialLanguage; label: string }[] = [
  { id: 'id', label: 'Indonesia' },
  { id: 'en', label: 'English' },
  { id: 'ar', label: 'العربية' },
];

export const SocialMediaPage: React.FC = () => {
  const [briefs, setBriefs] = useState<SocialBrief[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [mediaUrl, setMediaUrl] = useState('');
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [visualPrompt, setVisualPrompt] = useState('');
  const [generateImage, setGenerateImage] = useState(true);
  const [selectedLanguages, setSelectedLanguages] = useState<SocialLanguage[]>(['id', 'en', 'ar']);
  const [selectedPlatforms, setSelectedPlatforms] = useState<SocialPlatform[]>(['instagram', 'tiktok']);
  const { addToast } = useToast();

  const loadBriefs = useCallback(async (quiet = false) => {
    try {
      const response = await socialMediaApi.getBriefs(1, 20);
      setBriefs(response.data?.items || []);
    } catch (error) {
      if (!quiet) addToast('error', 'Unable to load the content workspace', error instanceof Error ? error.message : undefined);
    }
  }, [addToast]);

  useEffect(() => {
    loadBriefs();
    const poller = window.setInterval(() => loadBriefs(true), 4000);
    return () => window.clearInterval(poller);
  }, [loadBriefs]);

  const togglePlatform = (platform: SocialPlatform) => {
    setSelectedPlatforms((current) =>
      current.includes(platform)
        ? current.filter((item) => item !== platform)
        : [...current, platform],
    );
  };

  const toggleLanguage = (language: SocialLanguage) => {
    setSelectedLanguages((current) =>
      current.includes(language)
        ? current.filter((item) => item !== language)
        : [...current, language],
    );
  };

  const createBrief = async () => {
    if (!title.trim() || selectedPlatforms.length === 0 || selectedLanguages.length === 0) return;
    setIsCreating(true);
    try {
      let uploadedMediaUrl = mediaUrl.trim() || undefined;
      if (mediaFile) {
        const upload = await socialMediaApi.uploadAsset(mediaFile);
        uploadedMediaUrl = upload.data.signed_url;
      }
      const payload: CreateSocialBriefRequest = {
      title: title.trim(),
      objective: objective.trim() || undefined,
      target_platforms: selectedPlatforms,
      languages: selectedLanguages,
      media_url: uploadedMediaUrl,
      generate_image: generateImage && !uploadedMediaUrl,
      image_model: 'flux-realism',
      visual_prompt: visualPrompt.trim() || undefined,
      };
      const response = await socialMediaApi.createBrief(payload);
      setTitle('');
      setObjective('');
      setMediaUrl('');
      setMediaFile(null);
      setVisualPrompt('');
      await loadBriefs();
      addToast('success', 'Brief added to the generation queue', `Job ${response.data.id.slice(0, 8)} is creating platform variants and running QA.`);
    } catch (error) {
      addToast('error', 'Unable to create the brief', error instanceof Error ? error.message : undefined);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-2xl p-8 bg-[#0f172a] text-[#ffffff] shadow-xs">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1e293b] text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-[#8b5cf6]" />
            <span>Winsta AI Social Studio</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight leading-tight">
            Create once. <span className="text-[#8b5cf6]">Adapt everywhere.</span>
          </h2>
          <p className="text-sm text-[#cbd5e1] mt-3 leading-relaxed">
            Turn a brief or an approved trend into platform-ready social content. Generation, QA, approval, scheduling, and publishing live in one workflow.
          </p>
          <Button variant="primary" className="mt-6" onClick={() => document.getElementById('social-brief-form')?.scrollIntoView({ behavior: 'smooth' })} leftIcon={<Plus className="w-4 h-4" />}>
            Create a brief
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div id="social-brief-form">
          <Card className="p-6 bg-[#ffffff] lg:col-span-1">
          <div className="flex items-center gap-2 mb-5">
            <Send className="w-4 h-4 text-[#8b5cf6]" />
            <h3 className="font-bold">New content brief</h3>
          </div>
          <div className="space-y-4">
            <label className="block text-xs font-bold text-[#64748b]">
              Brief title
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Example: Launch the AI Image Tool" className="mt-2 w-full rounded-xl border border-[#e2e8f0] px-3 py-2.5 text-sm font-normal outline-none focus:border-[#0f172a]" />
            </label>
            <label className="block text-xs font-bold text-[#64748b]">
              Visual direction <span className="font-normal text-[#94a3b8]">(optional)</span>
              <textarea value={visualPrompt} onChange={(event) => setVisualPrompt(event.target.value)} placeholder="Editorial product scene, warm natural light, no text or logos" rows={2} className="mt-2 w-full rounded-xl border border-[#e2e8f0] px-3 py-2.5 text-sm font-normal outline-none focus:border-[#0f172a]" />
            </label>
            <label className="flex items-start gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-3 text-xs font-bold text-[#0f172a]">
              <input type="checkbox" checked={generateImage} disabled={Boolean(mediaUrl.trim() || mediaFile)} onChange={(event) => setGenerateImage(event.target.checked)} className="mt-0.5" />
              <span>Generate AI visuals automatically<span className="mt-1 block font-normal text-[#64748b]">Creates a rendition matching each platform aspect ratio. YouTube visuals are rendered into a vertical MP4 Short automatically.</span></span>
            </label>
            <div>
              <p className="mb-2 text-xs font-bold text-[#64748b]">Content languages</p>
              <div className="flex flex-wrap gap-2">
                {languages.map((language) => (
                  <button key={language.id} type="button" dir={language.id === 'ar' ? 'rtl' : 'ltr'} onClick={() => toggleLanguage(language.id)} className={`rounded-full border px-3 py-2 text-xs font-bold transition-colors ${selectedLanguages.includes(language.id) ? 'border-[#8b5cf6] bg-[#ede9fe] text-[#5b21b6]' : 'border-[#e2e8f0] bg-white text-[#64748b]'}`}>
                    {language.label}
                  </button>
                ))}
              </div>
            </div>
            <label className="block text-xs font-bold text-[#64748b]">
              Objective
              <textarea value={objective} onChange={(event) => setObjective(event.target.value)} placeholder="What should this content achieve?" rows={3} className="mt-2 w-full rounded-xl border border-[#e2e8f0] px-3 py-2.5 text-sm font-normal outline-none focus:border-[#0f172a]" />
            </label>
            <label className="block text-xs font-bold text-[#64748b]">
              Upload media to Supabase <span className="font-normal text-[#94a3b8]">(optional)</span>
              <span className="mt-2 flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-[#cbd5e1] bg-[#f8fafc] px-3 py-3 font-normal hover:border-[#8b5cf6]">
                <UploadCloud className="h-5 w-5 text-[#8b5cf6]" />
                <span className="min-w-0 flex-1 truncate">{mediaFile ? mediaFile.name : 'Choose JPG, PNG, WebP, or MP4 (max 50 MB)'}</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,video/mp4"
                  className="sr-only"
                  onChange={(event) => {
                    const selected = event.target.files?.[0] || null;
                    if (selected && selected.size > 50 * 1024 * 1024) {
                      addToast('error', 'Media file is larger than 50 MB');
                      event.target.value = '';
                      return;
                    }
                    setMediaFile(selected);
                    if (selected) setMediaUrl('');
                  }}
                />
              </span>
            </label>
            <label className="block text-xs font-bold text-[#64748b]">
              Or import from URL <span className="font-normal text-[#94a3b8]">(optional)</span>
              <input value={mediaUrl} disabled={Boolean(mediaFile)} onChange={(event) => setMediaUrl(event.target.value)} placeholder="https://cdn.example.com/creative.jpg" type="url" className="mt-2 w-full rounded-xl border border-[#e2e8f0] px-3 py-2.5 text-sm font-normal outline-none focus:border-[#0f172a] disabled:bg-[#f1f5f9]" />
              <span className="mt-1 block text-[10px] font-normal leading-relaxed text-[#94a3b8]">The backend mirrors imported media into private Supabase Storage.</span>
            </label>
            <div>
              <p className="text-xs font-bold text-[#64748b] mb-2">Target platforms</p>
              <div className="flex flex-wrap gap-2">
                {platforms.map((platform) => (
                  <button key={platform.id} type="button" onClick={() => togglePlatform(platform.id)} className={`px-3 py-2 rounded-full text-xs font-bold border transition-colors ${selectedPlatforms.includes(platform.id) ? 'bg-[#0f172a] text-white border-[#0f172a]' : 'bg-white text-[#64748b] border-[#e2e8f0]'}`}>
                    {platform.label}
                  </button>
                ))}
              </div>
            </div>
            <Button variant="primary" className="w-full" disabled={isCreating || !title.trim() || selectedPlatforms.length === 0 || selectedLanguages.length === 0} onClick={createBrief}>
              {isCreating ? (mediaFile ? 'Uploading & queueing...' : 'Queueing...') : 'Generate content'}
            </Button>
          </div>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold tracking-tight">Content workspace</h3>
              <p className="text-xs text-[#64748b]">Briefs and social generation jobs</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => loadBriefs()} rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>Refresh</Button>
          </div>
          {briefs.length > 0 ? briefs.map((brief) => (
            <Card key={brief.id} className="p-0 bg-[#ffffff] overflow-hidden">
              <div className="p-5 flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Image className="w-4 h-4 text-[#8b5cf6]" />
                    <h4 className="font-bold truncate">{brief.title}</h4>
                  </div>
                  <p className="text-xs text-[#64748b] mt-2">{brief.objective || 'No objective provided'} • {brief.target_platforms.join(', ')} • {(brief.target_languages || [brief.language]).join(', ').toUpperCase()}</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[10px] uppercase font-bold tracking-wide px-2 py-1 rounded-full ${brief.status === 'ready_for_review' ? 'bg-[#8b5cf6] text-[#0f172a]' : 'bg-[#f8fafc] text-[#64748b]'}`}>{brief.status.replaceAll('_', ' ')}</span>
                  <CalendarClock className="w-4 h-4 text-[#94a3b8]" />
                </div>
              </div>
              {brief.content_items.map((item) => (
                <div key={item.id} className="border-t border-[#e2e8f0] bg-[#f8fafc] p-5">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[#68a600]" /><span className="text-xs font-bold">{item.variants.length} variants generated • QA completed</span></div>
                    {item.status === 'ready_for_approval' && <Link to="/social/approvals" className="inline-flex items-center gap-1 text-xs font-bold text-[#0f172a] hover:underline">Review now <ArrowRight className="h-3.5 w-3.5" /></Link>}
                    {item.status === 'approved' && <Link to="/social/calendar" className="inline-flex items-center gap-1 text-xs font-bold text-[#0f172a] hover:underline">Schedule <ArrowRight className="h-3.5 w-3.5" /></Link>}
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {item.variants.map((variant) => (
                      <div key={variant.id} className="rounded-xl border border-[#e2e8f0] bg-white px-3 py-2">
                        {variant.media_ref && variant.platform === 'youtube' ? (
                          <video src={variant.media_ref} className="mb-2 aspect-[9/16] w-full rounded-lg bg-black object-contain" controls preload="metadata" />
                        ) : variant.media_ref ? (
                          <img src={variant.media_ref} alt={variant.visual_prompt || `${variant.platform} creative`} className="mb-2 aspect-video w-full rounded-lg object-cover" loading="lazy" />
                        ) : null}
                        <div className="flex items-center justify-between"><span className="text-[10px] font-black uppercase">{variant.platform} · {variant.language}</span><span className="text-[9px] font-bold text-[#68a600]">QA {variant.qa_result?.score ?? 100}</span></div>
                        <p dir={variant.language === 'ar' ? 'rtl' : 'ltr'} className="mt-1 line-clamp-3 text-xs leading-relaxed text-[#64748b]">{variant.caption}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </Card>
          )) : (
            <Card className="p-10 bg-[#ffffff] text-center">
              <Sparkles className="w-8 h-8 text-[#94a3b8] mx-auto mb-3" />
              <p className="font-bold">No social briefs yet</p>
              <p className="text-xs text-[#64748b] mt-1">Create a brief to start the Social Media Agent workflow.</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
