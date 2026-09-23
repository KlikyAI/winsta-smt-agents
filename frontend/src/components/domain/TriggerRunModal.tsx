import React, { useState, useMemo } from 'react';
import {
  Play,
  Globe,
  Palette,
  Clock,
  Check,
  Sparkles,
  HelpCircle,
  Search,
  ChevronDown,
  Tag,
  Compass,
  Cpu,
  Shirt,
  Utensils,
  Activity,
  Building2,
  Briefcase,
  Gamepad2,
  Leaf,
  Zap,
  Gem,
  Film,
  Sun,
  Flame,
  TrendingUp,
  Layers,
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { PlatformLogo } from '../common/PlatformLogo';
import type { CreateTrendRunRequest } from '../../types/trendRun';
import { trendRunsApi } from '../../api/trendRuns';
import { useToast } from '../../context/ToastContext';
import {
  COUNTRIES,
  CATEGORIES,
  AESTHETICS,
  TIME_WINDOWS,
} from '../../constants/discoveryOptions';

interface TriggerRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunCreated: () => void;
}

export const TriggerRunModal: React.FC<TriggerRunModalProps> = ({
  isOpen,
  onClose,
  onRunCreated,
}) => {
  const { addToast } = useToast();

  // 4 Core Parameters
  const [country, setCountry] = useState('ID');
  const [category, setCategory] = useState('beauty_skincare');
  const [aesthetic, setAesthetic] = useState('minimalist_organic');
  const [timeWindow, setTimeWindow] = useState('24h');

  // Country Search Dropdown State
  const [isCountryDropdownOpen, setIsCountryDropdownOpen] = useState(false);
  const [countrySearch, setCountrySearch] = useState('');

  // Platform Sources
  const [sources, setSources] = useState<string[]>([
    'google_trends',
    'tiktok',
    'instagram',
    'youtube',
    'x',
    'linkedin',
  ]);
  const [limit] = useState(25);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Quick Preset Countries for instant 1-click
  const quickCountries = ['ID', 'US', 'JP', 'SG', 'GLOBAL'];

  const filteredCountries = useMemo(() => {
    if (!countrySearch.trim()) return COUNTRIES;
    const query = countrySearch.toLowerCase();
    return COUNTRIES.filter(
      (c) =>
        c.name.toLowerCase().includes(query) ||
        c.code.toLowerCase().includes(query) ||
        c.region.toLowerCase().includes(query)
    );
  }, [countrySearch]);

  const selectedCountryObj = useMemo(
    () => COUNTRIES.find((c) => c.code === country) || COUNTRIES[0],
    [country]
  );

  const availableSources = [
    { id: 'google_trends', label: 'Google Trends', sub: 'Real-time search breakout', icon: '📈' },
    { id: 'tiktok', label: 'TikTok Trends', sub: 'Viral sounds & hashtags', icon: '🎵' },
    { id: 'instagram', label: 'Instagram Graph API', sub: 'Reels & Explore trends', icon: '📸' },
    { id: 'youtube', label: 'YouTube Shorts', sub: 'Trending short videos', icon: '▶️' },
    { id: 'x', label: 'X (Twitter)', sub: 'Real-time trending topics', icon: '🐦' },
    { id: 'linkedin', label: 'LinkedIn B2B', sub: 'Professional branding trends', icon: '💼' },
  ];

  const getCategoryIcon = (iconName: string) => {
    switch (iconName) {
      case 'Sparkles': return <Sparkles className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Shirt': return <Shirt className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Cpu': return <Cpu className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Utensils': return <Utensils className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Activity': return <Activity className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Building2': return <Building2 className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Briefcase': return <Briefcase className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Gamepad2': return <Gamepad2 className="w-4 h-4 text-[#8b5cf6]" />;
      default: return <Compass className="w-4 h-4 text-[#8b5cf6]" />;
    }
  };

  const getAestheticIcon = (iconName: string) => {
    switch (iconName) {
      case 'Leaf': return <Leaf className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Zap': return <Zap className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Gem': return <Gem className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Film': return <Film className="w-4 h-4 text-[#8b5cf6]" />;
      case 'Sun': return <Sun className="w-4 h-4 text-[#8b5cf6]" />;
      default: return <Palette className="w-4 h-4 text-[#8b5cf6]" />;
    }
  };

  const getTimeIcon = (iconName: string) => {
    switch (iconName) {
      case 'Flame': return <Flame className="w-4 h-4 text-[#8b5cf6]" />;
      case 'TrendingUp': return <TrendingUp className="w-4 h-4 text-[#8b5cf6]" />;
      default: return <Layers className="w-4 h-4 text-[#8b5cf6]" />;
    }
  };

  const toggleSource = (sourceId: string) => {
    setSources((prev) =>
      prev.includes(sourceId) ? prev.filter((s) => s !== sourceId) : [...prev, sourceId]
    );
  };

  const handleSelectAllSources = () => {
    setSources(availableSources.map((s) => s.id));
  };

  const handleTrigger = async () => {
    if (sources.length === 0) {
      addToast('error', 'Select Source', 'Please select at least one discovery source.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: CreateTrendRunRequest = {
        sources,
        market: country.toLowerCase(),
        country,
        category,
        aesthetic,
        time_window: timeWindow,
        language: selectedCountryObj?.defaultLang || 'en',
        limit_per_source: limit,
      };

      await trendRunsApi.createRun(payload);
      addToast(
        'success',
        'Targeted Discovery Run Queued',
        `Searching ${selectedCountryObj?.name || country} (${category}) with ${aesthetic} aesthetic.`
      );
      onRunCreated();
      onClose();
    } catch (err: any) {
      addToast('error', 'Failed to Trigger Discovery', err.message || 'An unexpected error occurred.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Targeted Trend Discovery Studio"
      description="Configure worldwide country targeting, industry niche, visual aesthetic styling, and time horizon."
      maxWidth="2xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <span className="text-xs text-slate-500 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#8b5cf6]" />
            Synthesizes 6-Modality AI Prompts Automatically
          </span>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleTrigger}
              isLoading={isSubmitting}
              leftIcon={<Play className="w-3.5 h-3.5 fill-[#a78bfa] text-[#a78bfa]" />}
            >
              Start Discovery ({sources.length} Sources)
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Parameter 1: Searchable Worldwide Country Selector */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-[#8b5cf6]" />
              1. Target Country / Region ({COUNTRIES.length} Countries Available)
            </label>
            <span className="text-[11px] text-slate-500">Sets Google Trends geo &amp; regional language</span>
          </div>

          {/* Quick Preset Buttons */}
          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1">
              Quick:
            </span>
            {quickCountries.map((qCode) => {
              const item = COUNTRIES.find((c) => c.code === qCode);
              if (!item) return null;
              const isSelected = country === item.code;
              return (
                <button
                  key={qCode}
                  type="button"
                  onClick={() => setCountry(item.code)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 border ${
                    isSelected
                      ? 'bg-[#0f172a] text-white border-[#0f172a] shadow-xs'
                      : 'bg-white text-slate-800 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  <span>{item.flag}</span>
                  <span>{item.name.split('/')[0].trim()}</span>
                  {isSelected && <Check className="w-3 h-3 text-[#a78bfa]" />}
                </button>
              );
            })}
          </div>

          {/* Searchable Dropdown Button */}
          <div className="relative">
            <div
              onClick={() => setIsCountryDropdownOpen(!isCountryDropdownOpen)}
              className="p-3 rounded-2xl border border-slate-300 bg-white hover:border-[#8b5cf6] cursor-pointer flex items-center justify-between transition-colors shadow-xs"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{selectedCountryObj.flag}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{selectedCountryObj.name}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono font-bold">
                      {selectedCountryObj.code}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Region: {selectedCountryObj.region} • Language: {selectedCountryObj.defaultLang.toUpperCase()}
                  </p>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </div>

            {/* Dropdown Menu */}
            {isCountryDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-2 p-2 rounded-2xl bg-white border border-slate-200 shadow-xl z-50 max-h-64 overflow-hidden flex flex-col">
                <div className="relative mb-2">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search country or code..."
                    value={countrySearch}
                    onChange={(e) => setCountrySearch(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
                    autoFocus
                  />
                </div>

                <div className="overflow-y-auto space-y-1 custom-scrollbar flex-1">
                  {filteredCountries.length > 0 ? (
                    filteredCountries.map((c) => {
                      const isSelected = country === c.code;
                      return (
                        <div
                          key={c.code}
                          onClick={() => {
                            setCountry(c.code);
                            setIsCountryDropdownOpen(false);
                            setCountrySearch('');
                          }}
                          className={`p-2.5 rounded-xl cursor-pointer flex items-center justify-between transition-colors ${
                            isSelected
                              ? 'bg-[#0f172a] text-white'
                              : 'hover:bg-slate-50 text-slate-800'
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <span className="text-xl">{c.flag}</span>
                            <span className="text-xs font-bold truncate">{c.name}</span>
                            <span className={`text-[10px] px-1.5 py-0.2 rounded border ${
                              isSelected ? 'border-white/20 text-[#a78bfa]' : 'border-slate-200 text-slate-500'
                            }`}>
                              {c.region}
                            </span>
                          </div>
                          {isSelected && <Check className="w-4 h-4 text-[#a78bfa]" />}
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-4 text-center text-xs text-slate-400">
                      No country matching "{countrySearch}"
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Parameter 2: Industry Category */}
        <div className="pt-3 border-t border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5 text-[#8b5cf6]" />
              2. Industry Niche / Category
            </label>
            <span className="text-[11px] text-slate-500">Focuses trending keyword cluster</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {CATEGORIES.slice(1).map((cat) => {
              const isSelected = category === cat.id;
              return (
                <div
                  key={cat.id}
                  onClick={() => setCategory(cat.id)}
                  className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-start justify-between ${
                    isSelected
                      ? 'bg-[#0f172a] border-[#0f172a] text-white shadow-xs'
                      : 'bg-white border-slate-200 hover:border-slate-400 text-slate-800'
                  }`}
                >
                  <div className="flex items-start gap-2.5 min-w-0">
                    <div className={`p-1.5 rounded-lg shrink-0 mt-0.5 ${isSelected ? 'bg-white/10' : 'bg-purple-50'}`}>
                      {getCategoryIcon(cat.iconName)}
                    </div>
                    <div className="min-w-0">
                      <h5 className={`text-xs font-bold truncate ${isSelected ? 'text-white' : 'text-slate-900'}`}>
                        {cat.label}
                      </h5>
                      <p className={`text-[10px] truncate ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                        {cat.description}
                      </p>
                    </div>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-[#a78bfa] shrink-0 ml-1 mt-0.5" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Parameter 3: Visual Aesthetic & Vibe */}
        <div className="pt-3 border-t border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Palette className="w-3.5 h-3.5 text-[#8b5cf6]" />
              3. Visual Aesthetic &amp; Vibe (AI Prompt Style)
            </label>
            <span className="text-[11px] text-slate-500">Directs Midjourney / Sora styling</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {AESTHETICS.map((aes) => {
              const isSelected = aesthetic === aes.id;
              return (
                <div
                  key={aes.id}
                  onClick={() => setAesthetic(aes.id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-start justify-between ${
                    isSelected
                      ? 'bg-white border-[#8b5cf6] shadow-sm ring-1 ring-[#8b5cf6]'
                      : 'bg-slate-50 border-slate-200 hover:border-slate-400'
                  }`}
                >
                  <div className="flex items-start gap-2.5 min-w-0">
                    <div className={`p-2 rounded-lg shrink-0 mt-0.5 ${isSelected ? 'bg-purple-100 text-[#8b5cf6]' : 'bg-slate-200/60'}`}>
                      {getAestheticIcon(aes.iconName)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <h5 className="text-xs font-bold text-slate-900">{aes.label}</h5>
                        {isSelected && (
                          <span className="px-1.5 py-0.2 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[9px] font-black uppercase">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 leading-snug mt-0.5">{aes.description}</p>
                    </div>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-[#8b5cf6] shrink-0 ml-1.5" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Parameter 4: Time Horizon */}
        <div className="pt-3 border-t border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#8b5cf6]" />
              4. Time Window / Trend Velocity
            </label>
            <span className="text-[11px] text-slate-500">Choose how fast the signal must move</span>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            {TIME_WINDOWS.map((t) => {
              const isSelected = timeWindow === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTimeWindow(t.id)}
                  className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-[#0f172a] border-[#0f172a] text-white shadow-xs'
                      : 'bg-white border-slate-200 hover:border-slate-400 text-slate-800'
                  }`}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-2">
                    <div className={`p-1.5 rounded-lg shrink-0 ${isSelected ? 'bg-white/10' : 'bg-purple-50'}`}>
                      {getTimeIcon(t.iconName)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-bold text-xs">
                        <span>{t.label}</span>
                      </div>
                      <p className={`mt-0.5 min-h-[2rem] text-[10px] leading-snug line-clamp-2 ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                        {t.sub}
                      </p>
                    </div>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-[#a78bfa] shrink-0 ml-1" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Parameter 5: Platform Sources */}
        <div className="pt-3 border-t border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-900">
              5. Monitored Platform Sources
            </label>
            <button
              type="button"
              onClick={handleSelectAllSources}
              className="text-xs text-[#8b5cf6] hover:underline font-semibold cursor-pointer"
            >
              Select All
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {availableSources.map((s) => {
              const isSelected = sources.includes(s.id);
              return (
                <div
                  key={s.id}
                  onClick={() => toggleSource(s.id)}
                  className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-white border-[#8b5cf6] shadow-xs'
                      : 'bg-slate-50 border-slate-200 opacity-75'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <PlatformLogo platform={s.id} size="sm" />
                    <span className="text-xs font-bold text-slate-900 truncate">{s.label}</span>
                  </div>

                  <div
                    className={`w-4 h-4 rounded-md border flex items-center justify-center transition-colors shrink-0 ml-1 ${
                      isSelected
                        ? 'bg-[#0f172a] border-[#0f172a] text-[#a78bfa]'
                        : 'border-slate-300 bg-white'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Summary Pill Banner */}
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-[#8b5cf6] shrink-0" />
          <p className="leading-snug">
            Targeting: <strong className="text-slate-900">{selectedCountryObj.flag} {selectedCountryObj.name}</strong> • Category: <strong className="text-slate-900">{CATEGORIES.find((c) => c.id === category)?.label}</strong> • Aesthetic: <strong className="text-slate-900">{AESTHETICS.find((a) => a.id === aesthetic)?.label}</strong> • Horizon: <strong className="text-slate-900">{TIME_WINDOWS.find((t) => t.id === timeWindow)?.label}</strong>
          </p>
        </div>
      </div>
    </Modal>
  );
};
