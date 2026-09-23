import React from 'react';
import type { TrendStatus } from '../../types/trend';
import type { TrendRunStatus } from '../../types/trendRun';
import { useLanguage } from '../../context/LanguageContext';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'lime' | 'orange' | 'ink' | 'paper' | 'cyan' | 'success';
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'sm',
  dot = false,
  className = '',
}) => {
  const sizeClasses = size === 'sm' ? 'px-2.5 py-0.5 text-[10px]' : 'px-3 py-1 text-xs';

  const variantClasses = {
    default: 'bg-slate-100 text-slate-700 border border-slate-200',
    lime: 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold',
    orange: 'bg-purple-50 text-purple-700 border border-purple-200 font-bold',
    ink: 'bg-[#0f172a] text-[#ffffff] border border-slate-800',
    paper: 'bg-white text-slate-800 border border-slate-200',
    cyan: 'bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold',
  }[variant];

  const dotColor = {
    default: 'bg-slate-400',
    lime: 'bg-emerald-500',
    orange: 'bg-[#8b5cf6] animate-pulse',
    ink: 'bg-[#a78bfa] animate-pulse',
    paper: 'bg-slate-400',
    cyan: 'bg-indigo-500',
    success: 'bg-emerald-500',
  }[variant];

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full whitespace-nowrap leading-none ${sizeClasses} ${variantClasses} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />}
      <span className="truncate">{children}</span>
    </span>
  );
};

export const TrendStatusBadge: React.FC<{ status: TrendStatus | string }> = ({ status }) => {
  const { t } = useLanguage();

  const config: Record<string, { labelKey: string; defaultLabel: string; variant: BadgeProps['variant'] }> = {
    discovered: { labelKey: 'status.discovered', defaultLabel: 'Discovered', variant: 'default' },
    analyzed: { labelKey: 'status.analyzed', defaultLabel: 'Analyzed', variant: 'cyan' },
    scored: { labelKey: 'status.scored', defaultLabel: 'Scored', variant: 'paper' },
    prompt_generated: { labelKey: 'status.prompts_ready', defaultLabel: 'Prompts Ready', variant: 'cyan' },
    prompts_generated: { labelKey: 'status.prompts_ready', defaultLabel: 'Prompts Ready', variant: 'cyan' },
    pending_review: { labelKey: 'status.pending_review', defaultLabel: 'Pending Review', variant: 'orange' },
    approved: { labelKey: 'status.approved', defaultLabel: 'Approved', variant: 'lime' },
    rejected: { labelKey: 'status.rejected', defaultLabel: 'Rejected', variant: 'ink' },
    archived: { labelKey: 'status.archived', defaultLabel: 'Archived', variant: 'default' },
  };

  const item = config[status] || {
    labelKey: `status.${status}`,
    defaultLabel: status ? status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : 'Unknown',
    variant: 'default',
  };

  return (
    <Badge size="sm" variant={item.variant} dot={status === 'pending_review' || status === 'approved'}>
      {t(item.labelKey, item.defaultLabel)}
    </Badge>
  );
};

export const TrendRunStatusBadge: React.FC<{ status: TrendRunStatus | string }> = ({ status }) => {
  const { t } = useLanguage();

  const config: Record<string, { labelKey: string; defaultLabel: string; variant: BadgeProps['variant'] }> = {
    queued: { labelKey: 'status.queued', defaultLabel: 'Queued', variant: 'default' },
    running: { labelKey: 'status.running', defaultLabel: 'Running', variant: 'orange' },
    completed: { labelKey: 'status.completed', defaultLabel: 'Completed', variant: 'lime' },
    partially_completed: { labelKey: 'status.partial', defaultLabel: 'Partial', variant: 'paper' },
    failed: { labelKey: 'status.failed', defaultLabel: 'Failed', variant: 'ink' },
    cancelled: { labelKey: 'status.cancelled', defaultLabel: 'Cancelled', variant: 'default' },
  };

  const item = config[status] || {
    labelKey: `status.${status}`,
    defaultLabel: status ? status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : 'Unknown',
    variant: 'default',
  };

  return (
    <Badge size="sm" variant={item.variant} dot={status === 'running'}>
      {t(item.labelKey, item.defaultLabel)}
    </Badge>
  );
};
