import React from 'react';

interface WinstaLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

export const WinstaLogo: React.FC<WinstaLogoProps> = ({
  size = 'md',
  showText = false,
  className = '',
}) => {
  const sizeMap = {
    sm: { box: 30, icon: 18, text: 'text-sm', sub: 'text-[9px]' },
    md: { box: 38, icon: 22, text: 'text-base', sub: 'text-[10px]' },
    lg: { box: 46, icon: 28, text: 'text-lg', sub: 'text-xs' },
    xl: { box: 58, icon: 36, text: 'text-xl', sub: 'text-xs' },
  };

  const currentSize = sizeMap[size];

  return (
    <div className={`inline-flex items-center gap-3 ${className}`}>
      {/* Sleek Modern Icon Badge */}
      <div
        className="relative shrink-0 flex items-center justify-center rounded-2xl bg-[#0f172a] text-[#ffffff] shadow-[2px_2px_0px_#0f172a] border border-[#1e293b] group-hover:scale-105 group-hover:shadow-[3px_3px_0px_#8b5cf6] transition-all duration-200"
        style={{ width: currentSize.box, height: currentSize.box }}
      >
        {/* Subtle Ambient Radial Highlight */}
        <div className="absolute inset-0 rounded-2xl bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-500/20 via-transparent to-transparent opacity-90" />

        {/* Minimalist Clean Modern Winsta Vector */}
        <svg
          viewBox="0 0 36 36"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative z-10"
          style={{ width: currentSize.icon, height: currentSize.icon }}
        >
          {/* Left Wing Segment */}
          <path
            d="M6 10.5C6 9.67157 6.67157 9 7.5 9H9.2C9.8 9 10.34 9.38 10.53 9.95L13.8 19.8L11.1 26.5C10.8 27.2 9.9 27.5 9.2 27.1L7.2 26C6.5 25.6 6 24.8 6 24V10.5Z"
            fill="url(#winsta-left-grad)"
          />

          {/* Right Wing Segment */}
          <path
            d="M30 10.5C30 9.67157 29.3284 9 28.5 9H26.8C26.2 9 25.66 9.38 25.47 9.95L22.2 19.8L24.9 26.5C25.2 27.2 26.1 27.5 26.8 27.1L28.8 26C29.5 25.6 30 24.8 30 24V10.5Z"
            fill="url(#winsta-right-grad)"
          />

          {/* Center Dynamic AI Apex (Upward Diamond Prism) */}
          <path
            d="M18 6.5L22.2 16.8L18 24.5L13.8 16.8L18 6.5Z"
            fill="#8b5cf6"
          />

          {/* Luminous Inner Core Prism Highlight */}
          <path
            d="M18 9L20.2 16.2L18 21.5L15.8 16.2L18 9Z"
            fill="#ffffff"
            fillOpacity="0.9"
          />

          {/* Modern Accent Micro Spark */}
          <circle cx="28.5" cy="7.5" r="1.8" fill="#a78bfa" />

          {/* Color Gradients */}
          <defs>
            <linearGradient id="winsta-left-grad" x1="6" y1="9" x2="14" y2="27" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="50%" stopColor="#c4b5fd" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
            <linearGradient id="winsta-right-grad" x1="30" y1="9" x2="22" y2="27" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="50%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#6366f1" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Typography Brand Name */}
      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5 leading-none">
            <h1 className={`font-serif font-extrabold tracking-tight text-[#0f172a] ${currentSize.text}`}>
              Winsta AI
            </h1>
            <span className="px-1.5 py-0.5 rounded-full bg-[#8b5cf6] text-[#ffffff] text-[9px] font-mono font-black uppercase tracking-wider leading-none shadow-xs">
              Studio
            </span>
          </div>
          <span className={`text-[#64748b] font-sans font-semibold tracking-wider uppercase ${currentSize.sub} mt-1`}>
            One AI Workspace
          </span>
        </div>
      )}
    </div>
  );
};
