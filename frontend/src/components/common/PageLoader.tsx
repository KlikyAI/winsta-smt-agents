import React from 'react';

export const PageLoader: React.FC<{ message?: string }> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] w-full py-16 animate-fade-in">
      <div className="relative flex items-center justify-center">
        {/* Outer glowing ring */}
        <div className="w-12 h-12 rounded-full border-2 border-purple-200 border-t-[#8b5cf6] animate-spin" />
        {/* Inner dot */}
        <div className="absolute w-4 h-4 rounded-full bg-[#0f172a]" />
      </div>
      <p className="mt-4 text-xs font-semibold text-slate-500 tracking-wide">
        {message}
      </p>
    </div>
  );
};

