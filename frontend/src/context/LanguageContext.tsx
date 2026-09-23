import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { type Language, LANGUAGES, translations } from '../i18n/translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, defaultText?: string) => string;
  dir: 'ltr' | 'rtl';
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('winsta_language');
    if (saved === 'en' || saved === 'ar' || saved === 'id') {
      return saved;
    }
    return 'en';
  });

  const activeLangOption = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];
  const dir = activeLangOption.dir;

  useEffect(() => {
    document.documentElement.dir = dir;
    document.documentElement.lang = language;
    if (language === 'ar') {
      document.body.classList.add('rtl-arabic');
    } else {
      document.body.classList.remove('rtl-arabic');
    }
  }, [language, dir]);

  const setLanguage = useCallback((newLang: Language) => {
    setLanguageState(newLang);
    localStorage.setItem('winsta_language', newLang);
  }, []);

  const t = useCallback(
    (key: string, defaultText?: string): string => {
      const langDict = translations[language] || translations.en;
      if (langDict && langDict[key]) {
        return langDict[key];
      }
      const enDict = translations.en;
      if (enDict && enDict[key]) {
        return enDict[key];
      }
      return defaultText || key;
    },
    [language]
  );

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, dir }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
