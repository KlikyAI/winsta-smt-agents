import React from 'react';
import {
  Copy,
  Check,
  Image as ImageIcon,
  Video,
  Mic,
  Palette,
  Film,
  Wand2,
} from 'lucide-react';
import { Button } from '../../common/Button';
import { useLanguage } from '../../../context/LanguageContext';

export type ModalityTab = 't2i' | 't2v' | 't2voice' | 'i2i' | 'i2v' | 'v2v';

interface ModalityTabContentProps {
  activeModality: ModalityTab;
  prompts: {
    t2i: string;
    t2v: string;
    t2voice: string;
    i2i: string;
    i2v: string;
    v2v: string;
    negative?: string | null;
  };
  copiedField: string | null;
  onCopy: (text: string, fieldName: string) => void;
  livePreviewSlot?: React.ReactNode;
  onRenderVisualPreview?: (promptText: string) => void;
  isGeneratingImage?: boolean;
}

export const ModalityTabContent: React.FC<ModalityTabContentProps> = ({
  activeModality,
  prompts,
  copiedField,
  onCopy,
  livePreviewSlot,
  onRenderVisualPreview,
  isGeneratingImage = false,
}) => {
  const { t } = useLanguage();

  return (
    <div className="space-y-4">
      {/* 1. Text to Image */}
      {activeModality === 't2i' && (
        <div className="p-5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
                <ImageIcon className="w-4 h-4 text-[#8b5cf6]" /> {t('prompt.t2i', '1. Text to Image')}
              </span>
              <span className="text-[10px] bg-[#f8fafc] border border-[#e2e8f0] text-[#64748b] px-2 py-0.5 rounded-full font-medium">
                Midjourney v6 / FLUX.1 / DALL-E 3
              </span>
            </div>

            <button
              onClick={() => onCopy(prompts.t2i, 't2i')}
              className="px-3 py-1.5 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1.5 transition-all cursor-pointer"
            >
              {copiedField === 't2i' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 't2i' ? t('prompt.copied', 'Copied!') : t('prompt.copy', 'Copy Prompt')}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-4 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#0f172a] leading-relaxed select-all">
            {prompts.t2i}
          </div>

          {livePreviewSlot}
        </div>
      )}

      {/* 2. Text to Video */}
      {activeModality === 't2v' && (
        <div className="p-5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs space-y-4">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
                <Video className="w-4 h-4 text-[#8b5cf6]" /> {t('prompt.t2v', '2. Text to Video')}
              </span>
              <span className="text-[10px] bg-[#f8fafc] border border-[#e2e8f0] text-[#64748b] px-2 py-0.5 rounded-full font-medium">
                OpenAI Sora / Haiper AI / Luma
              </span>
            </div>

            <button
              onClick={() => onCopy(prompts.t2v, 't2v')}
              className="px-3 py-1.5 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1.5 transition-all cursor-pointer"
            >
              {copiedField === 't2v' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 't2v' ? t('prompt.copied', 'Copied!') : t('prompt.copy', 'Copy Sora Prompt')}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-4 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#0f172a] leading-relaxed">
            {prompts.t2v}
          </div>

          {onRenderVisualPreview && (
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Want to render the starting visual keyframe?</span>
              <Button
                variant="light"
                size="sm"
                onClick={() => onRenderVisualPreview(prompts.t2v)}
                isLoading={isGeneratingImage}
                leftIcon={<Wand2 className="w-3.5 h-3.5 text-[#8b5cf6]" />}
              >
                {t('prompt.render_btn', 'Generate Visual Preview')}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* 3. Text to Voice */}
      {activeModality === 't2voice' && (
        <div className="p-5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
                <Mic className="w-4 h-4 text-[#8b5cf6]" /> {t('prompt.t2voice', '3. Text to Voice')}
              </span>
              <span className="text-[10px] bg-[#f8fafc] border border-[#e2e8f0] text-[#64748b] px-2 py-0.5 rounded-full font-medium">
                ElevenLabs / OpenAI TTS
              </span>
            </div>

            <button
              onClick={() => onCopy(prompts.t2voice, 't2voice')}
              className="px-3 py-1.5 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1.5 transition-all cursor-pointer"
            >
              {copiedField === 't2voice' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 't2voice' ? t('prompt.copied', 'Copied!') : t('prompt.copy', 'Copy Script')}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-4 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#0f172a] leading-relaxed">
            {prompts.t2voice}
          </div>
        </div>
      )}

      {/* 4. Image to Image */}
      {activeModality === 'i2i' && (
        <div className="p-5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs space-y-4">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
                <Palette className="w-4 h-4 text-[#8b5cf6]" /> {t('prompt.i2i', '4. Image to Image')}
              </span>
              <span className="text-[10px] bg-[#f8fafc] border border-[#e2e8f0] text-[#64748b] px-2 py-0.5 rounded-full font-medium">
                ControlNet / SDXL / Midjourney Remix
              </span>
            </div>

            <button
              onClick={() => onCopy(prompts.i2i, 'i2i')}
              className="px-3 py-1.5 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1.5 transition-all cursor-pointer"
            >
              {copiedField === 'i2i' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 'i2i' ? t('prompt.copied', 'Copied!') : t('prompt.copy', 'Copy I2I Prompt')}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-4 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#0f172a] leading-relaxed">
            {prompts.i2i}
          </div>

          {onRenderVisualPreview && (
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Render style transfer test preview:</span>
              <Button
                variant="light"
                size="sm"
                onClick={() => onRenderVisualPreview(prompts.i2i)}
                isLoading={isGeneratingImage}
                leftIcon={<Wand2 className="w-3.5 h-3.5 text-[#8b5cf6]" />}
              >
                {t('prompt.render_btn', 'Generate Visual Preview')}
              </Button>
            </div>
          )}
        </div>
      )}

      {/* 5. Image to Video */}
      {activeModality === 'i2v' && (
        <div className="p-5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
                <Film className="w-4 h-4 text-[#8b5cf6]" /> {t('prompt.i2v', '5. Image to Video')}
              </span>
              <span className="text-[10px] bg-[#f8fafc] border border-[#e2e8f0] text-[#64748b] px-2 py-0.5 rounded-full font-medium">
                Runway Gen-3 / Kling AI / Luma
              </span>
            </div>

            <button
              onClick={() => onCopy(prompts.i2v, 'i2v')}
              className="px-3 py-1.5 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1.5 transition-all cursor-pointer"
            >
              {copiedField === 'i2v' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 'i2v' ? t('prompt.copied', 'Copied!') : t('prompt.copy', 'Copy Motion Directives')}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-4 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#0f172a] leading-relaxed">
            {prompts.i2v}
          </div>
        </div>
      )}

      {/* 6. Video to Video */}
      {activeModality === 'v2v' && (
        <div className="p-5 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0f172a] flex items-center gap-1.5">
                <Video className="w-4 h-4 text-[#8b5cf6]" /> {t('prompt.v2v', '6. Video to Video')}
              </span>
              <span className="text-[10px] bg-[#f8fafc] border border-[#e2e8f0] text-[#64748b] px-2 py-0.5 rounded-full font-medium">
                DomoAI / Kaiber / Runway V2V
              </span>
            </div>

            <button
              onClick={() => onCopy(prompts.v2v, 'v2v')}
              className="px-3 py-1.5 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1.5 transition-all cursor-pointer"
            >
              {copiedField === 'v2v' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 'v2v' ? t('prompt.copied', 'Copied!') : t('prompt.copy', 'Copy V2V Prompt')}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-4 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#0f172a] leading-relaxed">
            {prompts.v2v}
          </div>
        </div>
      )}

      {/* Negative Prompt Filter Card */}
      {prompts.negative && (
        <div className="p-4 rounded-2xl bg-[#ffffff] border border-[#e2e8f0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8b5cf6]">
              Negative Prompt (Artifact & Quality Filter)
            </span>
            <button
              onClick={() => onCopy(prompts.negative || '', 'negative')}
              className="px-2.5 py-1 bg-[#f8fafc] hover:bg-[#0f172a] hover:text-white rounded-lg border border-[#e2e8f0] text-xs font-bold text-[#0f172a] flex items-center gap-1 transition-all cursor-pointer"
            >
              {copiedField === 'negative' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedField === 'negative' ? t('prompt.copied', 'Copied!') : 'Copy Negative'}
            </button>
          </div>

          <div className="bg-[#f8fafc] p-3 rounded-xl border border-[#e2e8f0] font-mono text-xs text-[#64748b] leading-relaxed">
            {prompts.negative}
          </div>
        </div>
      )}
    </div>
  );
};

