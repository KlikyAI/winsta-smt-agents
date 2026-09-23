import React, { useState, useEffect } from 'react';
import { Palette, Save, Sparkles } from 'lucide-react';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { socialMediaApi } from '../../../api/socialMedia';
import { useToast } from '../../../context/ToastContext';

export const BrandKitTab: React.FC = () => {
  const { addToast } = useToast();

  const [brandKit, setBrandKit] = useState({
    brandName: 'Winsta AI Studio',
    tagline: 'Autonomous AI Trend Intelligence & Social Content Studio',
    primaryColor: '#0f172a',
    accentColor: '#8b5cf6',
    secondaryColor: '#38bdf8',
    typography: 'Outfit, sans-serif',
    toneOfVoice: 'Luxury, Authoritative & Inspiring',
    targetAudience: 'Gulf Region (Kuwait, UAE, Saudi Arabia) & Global Innovators',
    hashtagsDefault: '#WinstaAI #FutureOfCreative #KuwaitTrends #LuxuryAI',
    disclaimer: 'Generated autonomously by Winsta AI Intelligence Engine. Human reviewed.',
    guidelines: 'Use verified facts, one clear CTA, and native phrasing for each language.',
    forbiddenTerms: '',
    requiredTerms: '',
    productFacts: '',
  });
  const [isSavingBrandKit, setIsSavingBrandKit] = useState(false);

  useEffect(() => {
    fetchBrandKit();
  }, []);

  const fetchBrandKit = async () => {
    try {
      const response = await socialMediaApi.getBrandKit();
      const data = response.data;
      if (!data) return;
      setBrandKit({
        brandName: data.brand_name,
        tagline: data.tagline || '',
        primaryColor: data.colors?.primary || '#0f172a',
        accentColor: data.colors?.accent || '#8b5cf6',
        secondaryColor: data.colors?.secondary || '#38bdf8',
        typography: data.fonts?.primary || 'Outfit, sans-serif',
        toneOfVoice: data.tone || '',
        targetAudience: data.target_audience || '',
        hashtagsDefault: (data.default_hashtags || []).join(' '),
        disclaimer: data.disclaimer || '',
        guidelines: data.guidelines || '',
        forbiddenTerms: (data.forbidden_terms || []).join(', '),
        requiredTerms: (data.required_terms || []).join(', '),
        productFacts: Object.entries(data.product_facts || {})
          .map(([key, value]) => `${key}=${String(value)}`)
          .join('\n'),
      });
    } catch {
      // Keep defaults available if backend is temporarily unreachable
    }
  };

  const handleSaveBrandKit = async () => {
    setIsSavingBrandKit(true);
    const splitTerms = (value: string) => value.split(/[,\n]/).map((item) => item.trim()).filter(Boolean);
    const productFacts = Object.fromEntries(
      brandKit.productFacts
        .split('\n')
        .map((line) => line.split('=', 2).map((part) => part.trim()))
        .filter(([key, value]) => Boolean(key && value)),
    );
    try {
      const response = await socialMediaApi.updateBrandKit({
        brand_name: brandKit.brandName,
        tagline: brandKit.tagline || undefined,
        colors: {
          primary: brandKit.primaryColor,
          accent: brandKit.accentColor,
          secondary: brandKit.secondaryColor,
        },
        fonts: { primary: brandKit.typography },
        tone: brandKit.toneOfVoice || undefined,
        target_audience: brandKit.targetAudience || undefined,
        default_hashtags: splitTerms(brandKit.hashtagsDefault.replaceAll(' ', ',')),
        disclaimer: brandKit.disclaimer || undefined,
        forbidden_terms: splitTerms(brandKit.forbiddenTerms),
        required_terms: splitTerms(brandKit.requiredTerms),
        product_facts: productFacts,
        languages: ['id', 'en', 'ar'],
        guidelines: brandKit.guidelines || undefined,
      });
      if (response.data) await fetchBrandKit();
      addToast('success', 'Brand Brain Updated', 'Versioned brand rules now apply to new AI social content.');
    } catch (error) {
      addToast('error', 'Unable to save Brand Brain', error instanceof Error ? error.message : undefined);
    } finally {
      setIsSavingBrandKit(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Palette className="w-4 h-4" />
            </span>
            <h3 className="text-lg font-bold tracking-tight text-slate-900">
              Brand Kit & Creative Style Guidelines
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Centralize logos, color palettes, tone of voice, and content presets applied across AI prompt generation and social media copy.
          </p>
        </div>
        <Button variant="lime" size="sm" onClick={handleSaveBrandKit} isLoading={isSavingBrandKit} leftIcon={<Save className="w-3.5 h-3.5" />}>
          Save Brand Kit
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Brand Config */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-6 bg-white border border-slate-200 space-y-4">
            <h4 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Brand Identity & Tone</h4>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Brand Name</label>
                <input
                  type="text"
                  value={brandKit.brandName}
                  onChange={(e) => setBrandKit({ ...brandKit, brandName: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Typography Font</label>
                <input
                  type="text"
                  value={brandKit.typography}
                  onChange={(e) => setBrandKit({ ...brandKit, typography: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Tone & Voice Preset</label>
              <select
                value={brandKit.toneOfVoice}
                onChange={(e) => setBrandKit({ ...brandKit, toneOfVoice: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
              >
                <option value="Luxury, Authoritative & Inspiring">Luxury, Authoritative & Inspiring (Gulf Premium)</option>
                <option value="Modern, Fast-Paced & Trendsetting">Modern, Fast-Paced & Trendsetting (Viral TikTok/Reels)</option>
                <option value="Executive, Professional & Insightful">Executive, Professional & Insightful (LinkedIn B2B)</option>
                <option value="Creative, Bold & Artistic">Creative, Bold & Artistic (Visual AI Prompts)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Default Hashtag Pool</label>
              <input
                type="text"
                value={brandKit.hashtagsDefault}
                onChange={(e) => setBrandKit({ ...brandKit, hashtagsDefault: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Target Audience</label>
              <textarea
                value={brandKit.targetAudience}
                onChange={(e) => setBrandKit({ ...brandKit, targetAudience: e.target.value })}
                rows={2}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Generation Guidelines</label>
              <textarea
                value={brandKit.guidelines}
                onChange={(e) => setBrandKit({ ...brandKit, guidelines: e.target.value })}
                rows={3}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Forbidden Terms</label>
                <textarea
                  value={brandKit.forbiddenTerms}
                  onChange={(e) => setBrandKit({ ...brandKit, forbiddenTerms: e.target.value })}
                  rows={3}
                  placeholder="guaranteed, cheapest"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Required Terms</label>
                <textarea
                  value={brandKit.requiredTerms}
                  onChange={(e) => setBrandKit({ ...brandKit, requiredTerms: e.target.value })}
                  rows={3}
                  placeholder="Winsta AI"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Verified Product Facts</label>
              <textarea
                value={brandKit.productFacts}
                onChange={(e) => setBrandKit({ ...brandKit, productFacts: e.target.value })}
                rows={3}
                placeholder={'product=Winsta AI\nmarket=Kuwait'}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-mono text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Required Disclaimer</label>
              <textarea
                value={brandKit.disclaimer}
                onChange={(e) => setBrandKit({ ...brandKit, disclaimer: e.target.value })}
                rows={2}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
              />
            </div>
          </Card>

          {/* Color Palette Tokens */}
          <Card className="p-6 bg-white border border-slate-200 space-y-4">
            <h4 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Color Palette Tokens</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Primary Color</label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={brandKit.primaryColor}
                    onChange={(e) => setBrandKit({ ...brandKit, primaryColor: e.target.value })}
                    className="w-8 h-8 rounded-lg cursor-pointer border-0 p-0"
                  />
                  <input
                    type="text"
                    value={brandKit.primaryColor}
                    onChange={(e) => setBrandKit({ ...brandKit, primaryColor: e.target.value })}
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-900"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Accent (Winsta Purple)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={brandKit.accentColor}
                    onChange={(e) => setBrandKit({ ...brandKit, accentColor: e.target.value })}
                    className="w-8 h-8 rounded-lg cursor-pointer border-0 p-0"
                  />
                  <input
                    type="text"
                    value={brandKit.accentColor}
                    onChange={(e) => setBrandKit({ ...brandKit, accentColor: e.target.value })}
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-900"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Secondary Cyan</label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={brandKit.secondaryColor}
                    onChange={(e) => setBrandKit({ ...brandKit, secondaryColor: e.target.value })}
                    className="w-8 h-8 rounded-lg cursor-pointer border-0 p-0"
                  />
                  <input
                    type="text"
                    value={brandKit.secondaryColor}
                    onChange={(e) => setBrandKit({ ...brandKit, secondaryColor: e.target.value })}
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-900"
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Live Brand Preview Card */}
        <div className="space-y-4">
          <Card className="p-6 bg-[#0f172a] text-white space-y-4 shadow-lg border-0">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-[#a78bfa]">Live Brand Preview</span>
              <Sparkles className="w-4 h-4 text-[#a78bfa]" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">{brandKit.brandName}</h3>
              <p className="text-xs text-[#cbd5e1] mt-1">{brandKit.tagline}</p>
            </div>
            <div className="p-3.5 rounded-xl bg-[#1e293b] border border-slate-700 space-y-2">
              <span className="text-[10px] font-bold uppercase text-[#7dd3fc]">Tone & Voice Prompt Injection</span>
              <p className="text-xs text-slate-300 font-medium italic">
                "{brandKit.toneOfVoice}"
              </p>
            </div>
            <div className="pt-2 flex flex-wrap gap-1.5">
              {brandKit.hashtagsDefault.split(' ').map((tag, idx) => (
                <span key={idx} className="px-2 py-0.5 rounded-md bg-purple-950/80 text-[#a78bfa] border border-purple-800 text-[10px] font-semibold">
                  {tag}
                </span>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

