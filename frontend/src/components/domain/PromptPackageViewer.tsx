import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  RefreshCw,
  Image as ImageIcon,
  Video,
  Mic,
  Palette,
  Film,
  Send,
  Tag,
} from 'lucide-react';
import type { PromptPackage } from '../../types/promptPackage';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { aiApi, type AIImageResponse } from '../../api/ai';
import { useToast } from '../../context/ToastContext';
import { useLanguage } from '../../context/LanguageContext';
import { LivePreviewCard } from './prompt/LivePreviewCard';
import { ModalityTabContent, type ModalityTab } from './prompt/ModalityTabContent';

interface PromptPackageViewerProps {
  packageData?: PromptPackage | null;
  allPackages?: PromptPackage[];
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  onSelectVersion?: (versionPkg: PromptPackage) => void;
}

export const PromptPackageViewer: React.FC<PromptPackageViewerProps> = ({
  packageData,
  allPackages = [],
  onRegenerate,
  isRegenerating = false,
  onSelectVersion,
}) => {
  const { addToast } = useToast();
  const { t } = useLanguage();
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [activeModality, setActiveModality] = useState<ModalityTab>('t2i');

  // Live Visual Preview State
  const [previewImage, setPreviewImage] = useState<AIImageResponse | null>(null);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [selectedAspectRatio, setSelectedAspectRatio] = useState<'16:9' | '1:1' | '9:16' | '4:5'>('16:9');

  useEffect(() => {
    setPreviewImage(null);
  }, [packageData?.id]);

  const handleCopy = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2200);
  };

  const handleGenerateVisual = async (promptText: string) => {
    const promptPackageId = packageData?.id;
    if (!promptText.trim() || !promptPackageId) return;
    setIsGeneratingImage(true);
    try {
      const res = await aiApi.generateImage({
        prompt_package_id: promptPackageId,
        prompt: promptText,
        aspect_ratio: selectedAspectRatio,
        model: 'cloudflare-flux',
      });
      setPreviewImage(res.data);
      addToast('success', 'AI Visual Rendered', `Visual generated via ${res.data.provider}`);
    } catch (err: any) {
      addToast('error', 'Visual Generation Failed', err.message || 'Failed to render image preview');
    } finally {
      setIsGeneratingImage(false);
    }
  };

  if (!packageData) {
    return (
      <div className="p-8 text-center bg-[#f8fafc] rounded-2xl border border-dashed border-[#e2e8f0]">
        <div className="w-12 h-12 rounded-full bg-white border border-[#e2e8f0] text-[#0f172a] flex items-center justify-center mx-auto mb-3 shadow-xs">
          <Sparkles className="w-6 h-6 text-[#8b5cf6]" />
        </div>
        <h4 className="text-base font-bold text-[#0f172a]">No Prompt Package Generated Yet</h4>
        <p className="text-xs text-[#64748b] mt-1.5 max-w-md mx-auto leading-relaxed">
          6-Modality AI prompt packages (Text-to-Image, Text-to-Video, Voice, Image-to-Image, Motion, Video-to-Video) are synthesized once trend score exceeds threshold.
        </p>
        {onRegenerate && (
          <Button
            variant="primary"
            size="sm"
            className="mt-5"
            onClick={onRegenerate}
            isLoading={isRegenerating}
            leftIcon={<Sparkles className="w-4 h-4 text-[#8b5cf6]" />}
          >
            Generate 6-Modality AI Prompts Now
          </Button>
        )}
      </div>
    );
  }

  // Modalities configuration
  const modalities: { id: ModalityTab; label: string; icon: React.ReactNode; badge: string }[] = [
    { id: 't2i', label: t('prompt.t2i', '1. Text to Image'), icon: <ImageIcon className="w-4 h-4" />, badge: 'Midjourney / FLUX.1' },
    { id: 't2v', label: t('prompt.t2v', '2. Text to Video'), icon: <Video className="w-4 h-4" />, badge: 'OpenAI Sora / Haiper' },
    { id: 't2voice', label: t('prompt.t2voice', '3. Text to Voice'), icon: <Mic className="w-4 h-4" />, badge: 'ElevenLabs / TTS' },
    { id: 'i2i', label: t('prompt.i2i', '4. Image to Image'), icon: <Palette className="w-4 h-4" />, badge: 'ControlNet / Remix' },
    { id: 'i2v', label: t('prompt.i2v', '5. Image to Video'), icon: <Film className="w-4 h-4" />, badge: 'Runway Gen-3 / Kling' },
    { id: 'v2v', label: t('prompt.v2v', '6. Video to Video'), icon: <Video className="w-4 h-4 text-[#8b5cf6]" />, badge: 'DomoAI / Kaiber V2V' },
  ];

  // Prompts dictionary
  const prompts = {
    t2i:
      packageData.text_to_image_prompt ||
      packageData.image_prompt ||
      'A hyper-detailed cinematic 8k key visual of Jakarta street food vendor stall under heavy rain, illuminated by glowing cyan and magenta neon signs, anamorphic lens flares, wet asphalt reflections, atmospheric mist, photorealistic render.',
    t2v:
      packageData.text_to_video_prompt ||
      'Cinematic wide shot: Steam rising from a traditional food cooking wok under heavy rain, neon lights flickering in water puddles, slow dolly forward with 60fps slow motion camera flow.',
    t2voice:
      packageData.text_to_voice_prompt ||
      '[Tone: Deep, Warm, Narrative] "When night falls in Jakarta, the rain doesn\'t stop the street life. Under neon lights and gentle rain drops, warmth is served fresh from the wok." [Pacing: Measured, Atmospheric]',
    i2i:
      packageData.image_to_image_prompt ||
      'Transform input image to cyberpunk aesthetic, enhance neon magenta and cyan contrast, add anamorphic rain streaks, wet asphalt surface reflection, 8k resolution style transfer --ar 16:9 --v 6.0',
    i2v:
      packageData.image_to_video_prompt ||
      'Gentle camera dolly forward through falling raindrops, steam rising from cooking wok, flickering neon reflections in water puddles, 24fps cinematic motion blur.',
    v2v:
      packageData.video_to_video_prompt ||
      'Convert source video to anime cyberpunk aesthetic, vibrant liquid neon overlay, keep human character motion intact, stylized cel-shaded rendering style transfer.',
    negative: packageData.negative_prompt,
  };

  const previewImageUrl =
    previewImage?.trend_reference_image_url ||
    previewImage?.image_url ||
    packageData.trend_reference_image_url;

  return (
    <div className="space-y-5">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-[#f8fafc] border border-[#e2e8f0]">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 bg-white border border-[#e2e8f0] rounded-full px-3 py-1 text-xs font-bold text-[#0f172a]">
            <Sparkles className="w-3.5 h-3.5 text-[#8b5cf6]" />
            <span>{t('prompt.package_version', '6-Modality AI Package')} v{packageData.version}</span>
          </div>

          <Badge variant="lime">
            {t('prompt.model', 'Model')}: {packageData.ai_model || 'GPT-4o Vision Engine'}
          </Badge>

          {allPackages.length > 1 && onSelectVersion && (
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <span>{t('prompt.history', 'History')}:</span>
              {allPackages.map((pkg) => (
                <button
                  key={pkg.id}
                  onClick={() => onSelectVersion(pkg)}
                  className={`px-2 py-0.5 rounded-md font-mono text-[11px] border transition-colors cursor-pointer ${
                    pkg.id === packageData.id
                      ? 'bg-[#0f172a] text-[#a78bfa] border-[#0f172a] font-bold'
                      : 'bg-white text-slate-500 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  v{pkg.version}
                </button>
              ))}
            </div>
          )}
        </div>

        {onRegenerate && (
          <Button
            variant="light"
            size="sm"
            onClick={onRegenerate}
            isLoading={isRegenerating}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isRegenerating ? 'animate-spin' : ''}`} />}
          >
            {isRegenerating ? t('prompt.synthesizing', 'Synthesizing Prompts...') : t('prompt.generate_variation', 'Generate New Variation')}
          </Button>
        )}
      </div>

      {/* Regeneration Progress Notice */}
      {isRegenerating && (
        <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 flex items-center gap-3 animate-pulse">
          <RefreshCw className="w-5 h-5 text-[#8b5cf6] animate-spin shrink-0" />
          <div>
            <h5 className="text-xs font-bold text-purple-900">{t('prompt.synthesis_in_progress', '6-Modality Prompt Synthesis In Progress')}</h5>
            <p className="text-[11px] text-purple-700">
              {t('prompt.synthesis_desc', 'Writing Text-to-Image, Text-to-Video, Voice Script, Image-to-Image, Motion, and Video-to-Video prompts...')}
            </p>
          </div>
        </div>
      )}

      {/* 6 Modality Tabs Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 border-b border-slate-200 pb-3">
        {modalities.map((tab) => {
          const isActive = activeModality === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveModality(tab.id)}
              className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-center transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#0f172a] text-[#a78bfa] border-[#0f172a] shadow-xs'
                  : 'bg-[#ffffff] text-slate-600 border-slate-200 hover:border-slate-400 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-1.5 font-bold text-xs">
                {tab.icon}
                <span className="truncate">{tab.label}</span>
              </div>
              <span className={`text-[9px] mt-1 font-medium truncate w-full ${isActive ? 'text-[#a78bfa]/80' : 'text-slate-400'}`}>
                {tab.badge}
              </span>
            </button>
          );
        })}
      </div>

      {/* Modality Prompt Display Cards */}
      <ModalityTabContent
        activeModality={activeModality}
        prompts={prompts}
        copiedField={copiedField}
        onCopy={handleCopy}
        onRenderVisualPreview={handleGenerateVisual}
        isGeneratingImage={isGeneratingImage}
        livePreviewSlot={
          <LivePreviewCard
            previewImage={previewImage}
            previewImageUrl={previewImageUrl}
            isGeneratingImage={isGeneratingImage}
            selectedAspectRatio={selectedAspectRatio}
            onAspectRatioChange={setSelectedAspectRatio}
            onGenerate={() => handleGenerateVisual(prompts.t2i)}
            fallbackPromptText={prompts.t2i}
            copiedField={copiedField}
            onCopy={handleCopy}
          />
        }
      />

      {/* Trend Hashtags & Metadata */}
      {packageData.tags && packageData.tags.length > 0 && (
        <div className="p-4 rounded-2xl bg-[#ffffff] border border-slate-200 shadow-xs">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5 mb-2.5">
            <Tag className="w-3.5 h-3.5 text-[#8b5cf6]" /> {t('prompt.hashtags', 'Recommended Publishing Hashtags')}
          </span>
          <div className="flex items-center gap-1.5 flex-wrap">
            {packageData.tags.map((tag, idx) => (
              <span
                key={idx}
                className="text-xs font-medium text-purple-700 bg-purple-50 border border-purple-200 px-3 py-1 rounded-full cursor-pointer hover:bg-purple-100 transition-colors"
                onClick={() => handleCopy(`#${tag}`, `tag-${idx}`)}
                title="Click to copy hashtag"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Downstream Dispatch Notice Banner */}
      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-[#0f172a] text-[#a78bfa] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
          <Send className="w-4 h-4" />
        </div>
        <div className="space-y-1">
          <h5 className="font-bold text-slate-900">{t('prompt.dispatch_notice_title', 'Where are these 6-Modality Prompts sent upon Approval?')}</h5>
          <p className="leading-relaxed">
            {t('prompt.dispatch_notice_sub', 'When you click "Review & Approve", this structured prompt package is automatically transmitted to:')}
          </p>
          <ul className="list-disc list-inside space-y-0.5 text-[11px] pt-1">
            <li><strong className="text-slate-900">Sarah Agent</strong>: {t('prompt.dispatch_notice_sarah', 'Receives visual, video motion, and voice scripts for autonomous asset creation.')}</li>
            <li><strong className="text-slate-900">Social Media Agent</strong>: {t('prompt.dispatch_notice_social', 'Formats captions, hashtags, and schedules multi-channel publishing.')}</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
