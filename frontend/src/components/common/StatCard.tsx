import React from 'react';
import { Card } from './Card';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  trendPositive?: boolean;
  subtitle?: string;
  color?: 'lime' | 'orange' | 'paper' | 'cyan' | 'ink';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  trend,
  trendPositive = true,
  subtitle,
  color = 'lime',
}) => {
  const iconBgs = {
    lime: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    orange: 'bg-amber-50 text-amber-600 border-amber-200',
    paper: 'bg-purple-50 text-[#8b5cf6] border-purple-200',
    cyan: 'bg-indigo-50 text-indigo-600 border-indigo-200',
    ink: 'bg-[#0f172a] text-[#a78bfa] border-slate-800',
  }[color];

  return (
    <Card className="relative group bg-white border border-slate-200 shadow-xs flex flex-col justify-between p-5 min-h-[128px]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <span className="clova-eyebrow text-slate-500 text-[10px] uppercase font-bold tracking-wider truncate block leading-tight">
            {title}
          </span>
          <h3 className="text-3xl font-bold font-sans text-slate-900 mt-2 tracking-tight leading-none">
            {value}
          </h3>
          {subtitle && (
            <p className="text-[11px] text-slate-500 mt-2 truncate font-medium">
              {subtitle}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-2xl border shadow-xs ${iconBgs} shrink-0 transition-transform group-hover:scale-105 duration-200`}>
          {icon}
        </div>
      </div>
      {trend && (
        <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center gap-1.5 text-xs font-semibold">
          <span className={trendPositive ? 'text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 text-[10px]' : 'text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200 text-[10px]'}>
            {trend}
          </span>
          <span className="text-slate-400 font-normal text-[11px]">vs previous cycle</span>
        </div>
      )}
    </Card>
  );
};
