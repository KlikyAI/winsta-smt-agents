import React from 'react';
import {
  Wand2,
  Check,
  Copy,
  ExternalLink,
  Download,
} from 'lucide-react';
import { Button } from '../../common/Button';
import type { AIImageResponse } from '../../../api/ai';
import { useLanguage } from '../../../context/LanguageContext';

interface LivePreviewCardProps {
  previewImage: AIImageResponse | null;
  previewImageUrl?: string;
  isGeneratingImage: boolean;
  selectedAspectRatio: '16:9' | '1:1' | '9:16' | '4:5';
  onAspectRatioChange: (ratio: '16:9' | '1:1' | '9:16' | '4:5') => void;
  onGenerate: () => void;
  fallbackPromptText: string;
  copiedField: string | null;
  onCopy: (text: string, fieldName: string) => void;
}

export const LivePreviewCard: React.FC<LivePreviewCardProps> = ({
  previewImage,
  previewImageUrl,
  isGeneratingImage,
  selectedAspectRatio,
  onAspectRatioChange,
  onGenerate,
  fallbackPromptText,
  copiedField,
  onCopy,
}) => {
  const { t } = useLanguage();

  return (
    <div className="pt-2 border-t border-slate-100">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-lg bg-purple-50 text-[#8b5cf6] border border-purple-100 flex items-center justify-center">
            <Wand2 className="w-3.5 h-3.5" />
          </span>
          <div>
            <h5 className="text-xs font-bold text-slate-900">
              {t('prompt.live_preview_title', 'Live AI Visual Render Preview')}
            </h5>
            <p className="text-[11px] text-slate-500">
              {t('prompt.live_preview_sub', 'Render a high-resolution photorealistic preview directly in studio')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedAspectRatio}
            onChange={(e) => onAspectRatioChange(e.target.value as any)}
            className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-bold text-slate-700 outline-none cursor-pointer"
          >
            <option value="16:9">16:9 Landscape</option>
            <option value="1:1">1:1 Square</option>
            <option value="9:16">9:16 Reel / Story</option>
            <option value="4:5">4:5 Feed Portrait</option>
          </select>

          <Button
            variant="primary"
            size="sm"
            onClick={onGenerate}
            isLoading={isGeneratingImage}
            leftIcon={<Wand2 className="w-3.5 h-3.5 text-[#a78bfa]" />}
          >
            {previewImageUrl
              ? t('prompt.rerender_btn', 'Re-render Visual')
              : t('prompt.render_btn', 'Generate Visual Preview')}
          </Button>
        </div>
      </div>

      {previewImageUrl && (
        <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-900 group shadow-md animate-fade-in mt-3">
          <img
            src={previewImageUrl}
            alt="AI Visual Preview"
            className="w-full h-auto max-h-[380px] object-cover transition-transform duration-300 group-hover:scale-[1.01]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 opacity-0 group-hover:opacity-100 transition-opacity p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[10px] font-bold border border-white/20">
                {previewImage
                  ? `${previewImage.provider} (${previewImage.aspect_ratio})`
                  : 'Saved reference image'}
              </span>
              <a
                href={previewImageUrl}
                target="_blank"
                rel="noreferrer"
                className="p-2 rounded-full bg-white/20 backdrop-blur-md text-white hover:bg-white hover:text-slate-900 transition-colors"
                title="Open Full Resolution"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <div className="flex items-center justify-between gap-3">
              <p className="text-[11px] text-white/90 truncate max-w-md font-mono">
                {previewImage?.prompt || fallbackPromptText}
              </p>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => onCopy(previewImageUrl, 'reference-url')}
                  className="px-3 py-1.5 rounded-lg bg-white/20 backdrop-blur-md text-white text-xs font-bold flex items-center gap-1.5 hover:bg-white hover:text-slate-900 transition-colors cursor-pointer"
                >
                  {copiedField === 'reference-url' ? (
                    <Check className="w-3.5 h-3.5" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  {copiedField === 'reference-url'
                    ? t('prompt.copied', 'Copied!')
                    : t('prompt.copy_public_url', 'Copy Public URL')}
                </button>
                <a
                  href={previewImageUrl}
                  download={`winsta-trend-${Date.now()}.jpg`}
                  className="px-3 py-1.5 rounded-lg bg-[#8b5cf6] text-white text-xs font-bold flex items-center gap-1.5 shadow-md hover:bg-[#7c3aed] transition-colors"
                >
                  <Download className="w-3.5 h-3.5" /> {t('prompt.download_asset', 'Download Asset')}
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

