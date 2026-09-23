import React from 'react';

interface AIProviderLogoProps {
  provider: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const AIProviderLogo: React.FC<AIProviderLogoProps> = ({
  provider,
  size = 'md',
  className = '',
}) => {
  const prov = provider.toLowerCase();

  const sizeClasses = {
    sm: 'w-6 h-6 p-1 text-xs',
    md: 'w-8 h-8 p-1.5 text-sm',
    lg: 'w-10 h-10 p-2 text-base',
    xl: 'w-12 h-12 p-2.5 text-lg',
  };

  // 1. DeepSeek (Official DeepSeek Blue Whale)
  if (prov === 'deepseek') {
    return (
      <div
        className={`rounded-xl bg-[#0066FF]/10 border border-[#0066FF]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
          <path
            d="M21.5 14.5C20.2 17.8 16.6 20 12.5 20C7.2 20 3 16 3 11C3 7.8 4.8 5 7.5 3.5C8 5.2 9.5 7.5 12 7.5C14.5 7.5 16 6 16.5 4.5C19.5 6.5 21.5 10 21.5 14.5Z"
            fill="#1D75F0"
          />
          <circle cx="8" cy="11" r="1.5" fill="#FFFFFF" />
          <path
            d="M17 14C16.5 15.5 14.5 17 12 17C9.5 17 8 15.8 7.5 15"
            stroke="#FFFFFF"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </svg>
      </div>
    );
  }

  // 2. OpenAI (Official OpenAI Rosette / Spiral Symbol)
  if (prov === 'openai') {
    return (
      <div
        className={`rounded-xl bg-[#10A37F]/10 border border-[#10A37F]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-[#10A37F]">
          <path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z" />
        </svg>
      </div>
    );
  }

  // 3. Anthropic Claude (Official Terracotta Asterisk / Spark)
  if (prov === 'anthropic' || prov === 'claude') {
    return (
      <div
        className={`rounded-xl bg-[#D97706]/10 border border-[#D97706]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-[#CC785C]">
          <path d="M17.47 3.5h-3.41l5.44 17h3.5zm-10.94 0l-5.53 17h3.55l1.32-4.14h5.63l1.32 4.14h3.55l-5.53-17zm-.26 10.22l1.9-5.96 1.9 5.96z" />
        </svg>
      </div>
    );
  }

  // 4. Google Gemini (Official 4-Point Gradient Sparkle)
  if (prov === 'gemini' || prov === 'google') {
    return (
      <div
        className={`rounded-xl bg-gradient-to-tr from-[#1B72E8]/10 via-[#8E75FF]/15 to-[#F35325]/10 border border-[#8E75FF]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
          <defs>
            <linearGradient id="gemini-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1B72E8" />
              <stop offset="50%" stopColor="#8E75FF" />
              <stop offset="100%" stopColor="#D96570" />
            </linearGradient>
          </defs>
          <path
            d="M12 2C12 7.52285 7.52285 12 2 12C7.52285 12 12 16.4771 12 22C12 16.4771 16.4771 12 22 12C16.4771 12 12 7.52285 12 2Z"
            fill="url(#gemini-grad)"
          />
        </svg>
      </div>
    );
  }

  // 5. Groq (Official Bold Orange-Red Groq Logo)
  if (prov === 'groq') {
    return (
      <div
        className={`rounded-xl bg-[#F05A28]/10 border border-[#F05A28]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
          <circle cx="12" cy="12" r="9" stroke="#F05A28" strokeWidth="3" />
          <path d="M12 7V12L16 14" stroke="#F05A28" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="12" cy="12" r="2.5" fill="#F05A28" />
        </svg>
      </div>
    );
  }

  // 6. Ollama (Official Ollama Llama Mascot Badge)
  if (prov === 'ollama') {
    return (
      <div
        className={`rounded-xl bg-[#1e293b]/10 border border-[#334155]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-slate-800">
          <path d="M9 3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v4h1a3 3 0 0 1 3 3v2a3 3 0 0 1-1 2.23V19a2 2 0 0 1-2 2h-1a1 1 0 0 1-1-1v-4h-2v4a1 1 0 0 1-1 1H8a2 2 0 0 1-2-2v-4.77A3 3 0 0 1 5 12v-2a3 3 0 0 1 3-3h1V3zm2 1h2v3h-2V4zm-3 5a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H8z" />
          <circle cx="9.5" cy="11.5" r="1" fill="#FFFFFF" />
          <circle cx="14.5" cy="11.5" r="1" fill="#FFFFFF" />
        </svg>
      </div>
    );
  }

  // 7. OpenRouter (Official OpenRouter Cyan-Purple Cubic Node)
  if (prov === 'openrouter') {
    return (
      <div
        className={`rounded-xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
          <path
            d="M12 2L3 7V17L12 22L21 17V7L12 2Z"
            stroke="#6366F1"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path
            d="M12 22V12M12 12L21 7M12 12L3 7"
            stroke="#38BDF8"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="12" r="2.5" fill="#6366F1" />
        </svg>
      </div>
    );
  }

  // 8. Mistral AI (Official Mistral Orange/Amber Staircase / Steps)
  if (prov === 'mistral') {
    return (
      <div
        className={`rounded-xl bg-[#FA520F]/10 border border-[#FA520F]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
          <rect x="3" y="4" width="4" height="4" fill="#FF7000" rx="0.5" />
          <rect x="17" y="4" width="4" height="4" fill="#FF7000" rx="0.5" />
          <rect x="3" y="8" width="4" height="4" fill="#FF8A00" rx="0.5" />
          <rect x="7" y="8" width="4" height="4" fill="#FF8A00" rx="0.5" />
          <rect x="13" y="8" width="4" height="4" fill="#FF8A00" rx="0.5" />
          <rect x="17" y="8" width="4" height="4" fill="#FF8A00" rx="0.5" />
          <rect x="3" y="12" width="4" height="4" fill="#FFA500" rx="0.5" />
          <rect x="7" y="12" width="4" height="4" fill="#FFA500" rx="0.5" />
          <rect x="10" y="12" width="4" height="4" fill="#FFA500" rx="0.5" />
          <rect x="13" y="12" width="4" height="4" fill="#FFA500" rx="0.5" />
          <rect x="17" y="12" width="4" height="4" fill="#FFA500" rx="0.5" />
          <rect x="3" y="16" width="4" height="4" fill="#FA520F" rx="0.5" />
          <rect x="17" y="16" width="4" height="4" fill="#FA520F" rx="0.5" />
        </svg>
      </div>
    );
  }

  // 9. LiteLLM (Lightning / Flame Proxy Symbol)
  if (prov === 'litellm') {
    return (
      <div
        className={`rounded-xl bg-[#3B82F6]/10 border border-[#3B82F6]/20 flex items-center justify-center shrink-0 shadow-xs ${sizeClasses[size]} ${className}`}
      >
        <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full text-[#3B82F6]">
          <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" />
        </svg>
      </div>
    );
  }

  // Fallback Generic AI Bot Logo
  return (
    <div
      className={`rounded-xl bg-purple-50 text-[#8b5cf6] border border-purple-100 flex items-center justify-center shrink-0 font-bold text-xs uppercase ${sizeClasses[size]} ${className}`}
    >
      {provider.substring(0, 2)}
    </div>
  );
};
