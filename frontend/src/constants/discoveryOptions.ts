/**
 * Comprehensive World Country Database & Discovery Presets
 */

export interface CountryOption {
  code: string;
  name: string;
  flag: string;
  region: string;
  defaultLang: string;
}

export interface CategoryOption {
  id: string;
  label: string;
  iconName: string;
  description: string;
}

export interface AestheticOption {
  id: string;
  label: string;
  iconName: string;
  description: string;
  promptModifier: string;
}

export interface TimeWindowOption {
  id: string;
  label: string;
  iconName: string;
  sub: string;
}

export const COUNTRIES: CountryOption[] = [
  // Worldwide
  { code: 'GLOBAL', name: 'Worldwide / All Countries', flag: '🌐', region: 'Global', defaultLang: 'en' },

  // Middle East (Timur Tengah)
  { code: 'SA', name: 'Saudi Arabia', flag: '🇸🇦', region: 'Middle East', defaultLang: 'ar' },
  { code: 'AE', name: 'United Arab Emirates', flag: '🇦🇪', region: 'Middle East', defaultLang: 'ar' },
  { code: 'QA', name: 'Qatar', flag: '🇶🇦', region: 'Middle East', defaultLang: 'ar' },
  { code: 'KW', name: 'Kuwait', flag: '🇰🇼', region: 'Middle East', defaultLang: 'ar' },
  { code: 'BH', name: 'Bahrain', flag: '🇧🇭', region: 'Middle East', defaultLang: 'ar' },
  { code: 'OM', name: 'Oman', flag: '🇴🇲', region: 'Middle East', defaultLang: 'ar' },
  { code: 'EG', name: 'Egypt', flag: '🇪🇬', region: 'Middle East', defaultLang: 'ar' },
  { code: 'JO', name: 'Jordan', flag: '🇯🇴', region: 'Middle East', defaultLang: 'ar' },
  { code: 'LB', name: 'Lebanon', flag: '🇱🇧', region: 'Middle East', defaultLang: 'ar' },
  { code: 'IQ', name: 'Iraq', flag: '🇮🇶', region: 'Middle East', defaultLang: 'ar' },
  { code: 'YE', name: 'Yemen', flag: '🇾🇪', region: 'Middle East', defaultLang: 'ar' },
  { code: 'SY', name: 'Syria', flag: '🇸🇾', region: 'Middle East', defaultLang: 'ar' },
  { code: 'PS', name: 'Palestine', flag: '🇵🇸', region: 'Middle East', defaultLang: 'ar' },
  { code: 'TR', name: 'Turkey', flag: '🇹🇷', region: 'Middle East', defaultLang: 'tr' },
  { code: 'IR', name: 'Iran', flag: '🇮🇷', region: 'Middle East', defaultLang: 'fa' },
  { code: 'IL', name: 'Israel', flag: '🇮🇱', region: 'Middle East', defaultLang: 'he' },

  // South Asia (Asia Selatan)
  { code: 'IN', name: 'India', flag: '🇮🇳', region: 'South Asia', defaultLang: 'en' },
  { code: 'PK', name: 'Pakistan', flag: '🇵🇰', region: 'South Asia', defaultLang: 'ur' },
  { code: 'BD', name: 'Bangladesh', flag: '🇧🇩', region: 'South Asia', defaultLang: 'bn' },
  { code: 'LK', name: 'Sri Lanka', flag: '🇱🇰', region: 'South Asia', defaultLang: 'si' },
  { code: 'NP', name: 'Nepal', flag: '🇳🇵', region: 'South Asia', defaultLang: 'ne' },
  { code: 'MV', name: 'Maldives', flag: '🇲🇻', region: 'South Asia', defaultLang: 'en' },
  { code: 'BT', name: 'Bhutan', flag: '🇧🇹', region: 'South Asia', defaultLang: 'dz' },
  { code: 'AF', name: 'Afghanistan', flag: '🇦🇫', region: 'South Asia', defaultLang: 'ps' },

  // Southeast Asia
  { code: 'ID', name: 'Indonesia', flag: '🇮🇩', region: 'Southeast Asia', defaultLang: 'id' },
  { code: 'MY', name: 'Malaysia', flag: '🇲🇾', region: 'Southeast Asia', defaultLang: 'ms' },
  { code: 'SG', name: 'Singapore', flag: '🇸🇬', region: 'Southeast Asia', defaultLang: 'en' },
  { code: 'TH', name: 'Thailand', flag: '🇹🇭', region: 'Southeast Asia', defaultLang: 'th' },
  { code: 'PH', name: 'Philippines', flag: '🇵🇭', region: 'Southeast Asia', defaultLang: 'en' },
  { code: 'VN', name: 'Vietnam', flag: '🇻🇳', region: 'Southeast Asia', defaultLang: 'vi' },

  // East Asia
  { code: 'JP', name: 'Japan', flag: '🇯🇵', region: 'East Asia', defaultLang: 'ja' },
  { code: 'KR', name: 'South Korea', flag: '🇰🇷', region: 'East Asia', defaultLang: 'ko' },
  { code: 'TW', name: 'Taiwan', flag: '🇹🇼', region: 'East Asia', defaultLang: 'zh' },
  { code: 'HK', name: 'Hong Kong', flag: '🇭🇰', region: 'East Asia', defaultLang: 'zh' },

  // North America
  { code: 'US', name: 'United States', flag: '🇺🇸', region: 'North America', defaultLang: 'en' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦', region: 'North America', defaultLang: 'en' },
  { code: 'MX', name: 'Mexico', flag: '🇲🇽', region: 'North America', defaultLang: 'es' },

  // Europe
  { code: 'GB', name: 'United Kingdom', flag: '🇬🇧', region: 'Europe', defaultLang: 'en' },
  { code: 'DE', name: 'Germany', flag: '🇩🇪', region: 'Europe', defaultLang: 'de' },
  { code: 'FR', name: 'France', flag: '🇫🇷', region: 'Europe', defaultLang: 'fr' },
  { code: 'IT', name: 'Italy', flag: '🇮🇹', region: 'Europe', defaultLang: 'it' },
  { code: 'ES', name: 'Spain', flag: '🇪🇸', region: 'Europe', defaultLang: 'es' },
  { code: 'NL', name: 'Netherlands', flag: '🇳🇱', region: 'Europe', defaultLang: 'nl' },
  { code: 'CH', name: 'Switzerland', flag: '🇨🇭', region: 'Europe', defaultLang: 'de' },
  { code: 'SE', name: 'Sweden', flag: '🇸🇪', region: 'Europe', defaultLang: 'sv' },
  { code: 'NO', name: 'Norway', flag: '🇳🇴', region: 'Europe', defaultLang: 'no' },
  { code: 'PL', name: 'Poland', flag: '🇵🇱', region: 'Europe', defaultLang: 'pl' },

  // Oceania
  { code: 'AU', name: 'Australia', flag: '🇦🇺', region: 'Oceania', defaultLang: 'en' },
  { code: 'NZ', name: 'New Zealand', flag: '🇳🇿', region: 'Oceania', defaultLang: 'en' },

  // Latin America
  { code: 'BR', name: 'Brazil', flag: '🇧🇷', region: 'Latin America', defaultLang: 'pt' },
  { code: 'AR', name: 'Argentina', flag: '🇦🇷', region: 'Latin America', defaultLang: 'es' },
  { code: 'CO', name: 'Colombia', flag: '🇨🇴', region: 'Latin America', defaultLang: 'es' },
  { code: 'CL', name: 'Chile', flag: '🇨🇱', region: 'Latin America', defaultLang: 'es' },

  // Africa
  { code: 'ZA', name: 'South Africa', flag: '🇿🇦', region: 'Africa', defaultLang: 'en' },
  { code: 'NG', name: 'Nigeria', flag: '🇳🇬', region: 'Africa', defaultLang: 'en' },
  { code: 'KE', name: 'Kenya', flag: '🇰🇪', region: 'Africa', defaultLang: 'en' },
  { code: 'MA', name: 'Morocco', flag: '🇲🇦', region: 'Africa', defaultLang: 'ar' },
];

export const CATEGORIES: CategoryOption[] = [
  { id: 'all', label: 'All Categories', iconName: 'Compass', description: 'Cross-industry breakout viral topics' },
  { id: 'beauty_skincare', label: 'Beauty & Skincare', iconName: 'Sparkles', description: 'Cosmetics, skincare routines, glow aesthetic' },
  { id: 'fashion_apparel', label: 'Fashion & Apparel', iconName: 'Shirt', description: 'Streetwear, lookbooks, runway styles' },
  { id: 'tech_ai', label: 'Tech, AI & Gadgets', iconName: 'Cpu', description: 'AI workflows, hardware, spatial computing' },
  { id: 'food_beverage', label: 'Food & Beverage', iconName: 'Utensils', description: 'Culinary creations, coffee, dining ASMR' },
  { id: 'fitness_wellness', label: 'Fitness & Wellness', iconName: 'Activity', description: 'Workouts, healthy living, mindfulness' },
  { id: 'interior_architecture', label: 'Interior & Decor', iconName: 'Building2', description: 'Modern homes, architecture, aesthetics' },
  { id: 'b2b_business', label: 'B2B & Marketing', iconName: 'Briefcase', description: 'Executive insights, brand strategy' },
  { id: 'gaming_entertainment', label: 'Gaming & Pop Culture', iconName: 'Gamepad2', description: 'Next-gen gaming, stream clips, entertainment' },
];

export const AESTHETIC_STYLES: AestheticOption[] = [
  {
    id: 'minimalist_organic',
    label: 'Minimalist & Organic',
    iconName: 'Leaf',
    description: 'Raw limestone, linen, soft sunlight, earthy calm palette',
    promptModifier: 'minimalist organic aesthetic, raw limestone texture, soft warm sunlight, linen drape, earth tones, clean composition',
  },
  {
    id: 'cyberpunk_neon',
    label: 'Cyberpunk & Neo-Noir',
    iconName: 'Zap',
    description: 'Glowing cyan-magenta neon, wet reflections, high-tech dark mood',
    promptModifier: 'cyberpunk neo-noir aesthetic, glowing cyan and magenta neon signs, wet asphalt reflections, volumetric atmosphere',
  },
  {
    id: 'luxury_editorial',
    label: 'Luxury High-Editorial',
    iconName: 'Gem',
    description: 'Liquid chrome, high-fashion studio lighting, glossy reflections',
    promptModifier: 'luxury high-fashion editorial aesthetic, liquid chrome accents, dramatic studio backlight, 8k commercial grading',
  },
  {
    id: 'vintage_retro',
    label: '90s Retro & Film Grain',
    iconName: 'Film',
    description: 'Analog VHS tape vibes, nostalgic 35mm warmth, lo-fi aesthetic',
    promptModifier: 'retro 90s aesthetic, analog VHS camcorder texture, subtle chromatic aberration, 35mm film grain, nostalgic warm color grade',
  },
  {
    id: 'warm_cinematic',
    label: 'Cinematic Golden Hour',
    iconName: 'Sun',
    description: 'Rich amber light, soft volumetric dust particles, anamorphic lens',
    promptModifier: 'cinematic golden hour lighting, rich warm shadows, atmospheric dust particles, natural depth of field, 35mm prime shot',
  },
  {
    id: 'bold_vibrant',
    label: 'Bold Pop & High Contrast',
    iconName: 'Palette',
    description: 'Ultra-vivid colors, dynamic key visual, studio pop art',
    promptModifier: 'bold vibrant pop art aesthetic, high saturation color harmony, dynamic punchy contrast, modern studio key visual',
  },
];

export const AESTHETICS = AESTHETIC_STYLES;

export const TIME_WINDOWS: TimeWindowOption[] = [
  { id: '24h', label: 'Last 24 Hours', iconName: 'Flame', sub: 'Catch the spark before it becomes the story.' },
  { id: '7d', label: 'Last 7 Days', iconName: 'TrendingUp', sub: 'Track momentum while audiences lean in.' },
  { id: '30d', label: 'Last 30 Days', iconName: 'Layers', sub: 'Spot durable themes before they go mainstream.' },
];
