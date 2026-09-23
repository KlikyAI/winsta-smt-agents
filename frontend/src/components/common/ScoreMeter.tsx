import React from 'react';

interface ScoreMeterProps {
  score?: number | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ScoreMeter: React.FC<ScoreMeterProps> = ({
  score = 0,
  size = 'md',
  showLabel = true,
}) => {
  const numericScore = score ? Math.round(score) : 0;

  if (size === 'sm') {
    return (
      <div className="flex items-center gap-2">
        <div className="w-16 h-2 bg-slate-100 border border-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#8b5cf6] rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, numericScore))}%` }}
          />
        </div>
        <span className="text-xs font-extrabold text-slate-900 font-mono">{numericScore}</span>
      </div>
    );
  }

  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-purple-200 bg-purple-50 text-purple-700 shadow-xs"
    >
      <span className="text-sm font-extrabold font-serif leading-none tracking-tight">{numericScore}</span>
      {showLabel && (
        <span className="text-[9px] uppercase font-extrabold tracking-widest text-purple-600">
          Pts
        </span>
      )}
    </div>
  );
};
