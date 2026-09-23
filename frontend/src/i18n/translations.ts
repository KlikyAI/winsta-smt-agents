import en from '../locales/en.json';
import ar from '../locales/ar.json';
import id from '../locales/id.json';

export type Language = 'en' | 'ar' | 'id';

export interface LanguageOption {
  code: Language;
  label: string;
  nativeLabel: string;
  flag: string;
  dir: 'ltr' | 'rtl';
}

export const LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', nativeLabel: 'English (US)', flag: '🇺🇸', dir: 'ltr' },
  { code: 'ar', label: 'Arabic', nativeLabel: 'العربية', flag: '🇸🇦', dir: 'rtl' },
  { code: 'id', label: 'Indonesian', nativeLabel: 'Bahasa Indonesia', flag: '🇮🇩', dir: 'ltr' },
];

export const translations: Record<Language, Record<string, string>> = {
  en,
  ar,
  id,
};

export type TranslationKey = keyof typeof en;
