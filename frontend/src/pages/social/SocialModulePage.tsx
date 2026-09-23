import React from 'react';
import {
  BarChart3,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  DollarSign,
  Link2,
  Megaphone,
  ShieldCheck,
} from 'lucide-react';
import { Card } from '../../components/common/Card';

export type SocialModuleSection = 'calendar' | 'approvals' | 'accounts' | 'analytics' | 'campaigns';

interface SocialModulePageProps {
  section: SocialModuleSection;
}

const moduleConfig: Record<SocialModuleSection, {
  eyebrow: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  accent: string;
  cards: Array<{ title: string; description: string; status: string }>;
}> = {
  calendar: {
    eyebrow: 'Publishing Operations',
    title: 'Calendar & Publishing',
    description: 'Review the publishing timeline, scheduled platform variants, delivery states, and retry-safe publish jobs.',
    icon: <CalendarDays className="w-7 h-7" />,
    accent: '#8b5cf6',
    cards: [
      { title: 'Content Calendar', description: 'Weekly and monthly view for approved scheduled content.', status: 'UI foundation' },
      { title: 'Publishing Queue', description: 'Track queued, publishing, published, and failed platform jobs.', status: 'Queue ready' },
      { title: 'Delivery Recovery', description: 'Retry failed jobs without creating duplicate social posts.', status: 'Idempotency ready' },
    ],
  },
  approvals: {
    eyebrow: 'Human Review',
    title: 'Social Approvals',
    description: 'Keep copy, creative variants, schedules, and high-impact actions behind an auditable review boundary.',
    icon: <ClipboardCheck className="w-7 h-7" />,
    accent: '#8b5cf6',
    cards: [
      { title: 'Content Review', description: 'Approve or reject generated content and platform variants.', status: 'API ready' },
      { title: 'Version Lock', description: 'Freeze the exact approved payload before scheduling and publishing.', status: 'Schema ready' },
      { title: 'Audit History', description: 'Record decision, reviewer, notes, and payload version.', status: 'Schema ready' },
    ],
  },
  accounts: {
    eyebrow: 'Platform Connections',
    title: 'Social Accounts',
    description: 'Manage official platform connections and keep credentials isolated from prompts and application logs.',
    icon: <Link2 className="w-7 h-7" />,
    accent: '#7dd3fc',
    cards: [
      { title: 'Instagram & Facebook', description: 'Meta professional accounts and publishing permissions.', status: 'Not connected' },
      { title: 'TikTok', description: 'Authorized Content Posting API connection and scopes.', status: 'Not connected' },
      { title: 'YouTube & X', description: 'Authorized channels/accounts for publishing and metrics.', status: 'Not connected' },
    ],
  },
  analytics: {
    eyebrow: 'Performance Intelligence',
    title: 'Social Analytics',
    description: 'Normalize supported platform metrics and return performance summaries to the Winsta dashboard and Sarah Agent.',
    icon: <BarChart3 className="w-7 h-7" />,
    accent: '#c4b5fd',
    cards: [
      { title: 'Post Performance', description: 'Reach, impressions, engagement, clicks, and supported conversions.', status: 'Sync foundation' },
      { title: 'Platform Comparison', description: 'Compare normalized outcomes without fabricating unavailable metrics.', status: 'Pending data' },
      { title: 'Recommendations', description: 'Generate evidence-based optimization suggestions after metrics sync.', status: 'Pending data' },
    ],
  },
  campaigns: {
    eyebrow: 'Paid Social',
    title: 'Paid Campaigns',
    description: 'Prepare campaign plans and auditable mutation commands before any approved marketing API execution.',
    icon: <DollarSign className="w-7 h-7" />,
    accent: '#fbbf24',
    cards: [
      { title: 'Campaign Planner', description: 'Objective, audience, budget cap, placements, creative, and schedule.', status: 'Foundation' },
      { title: 'Budget Approval', description: 'Require explicit approval before launch or budget-changing actions.', status: 'Guardrail defined' },
      { title: 'Campaign Operations', description: 'Launch, pause, update, and reconcile supported platform campaigns.', status: 'API pending' },
    ],
  },
};

export const SocialModulePage: React.FC<SocialModulePageProps> = ({ section }) => {
  const config = moduleConfig[section];

  return (
    <div className="space-y-8">
      <div className="relative overflow-hidden rounded-2xl p-8 bg-[#0f172a] text-[#ffffff] shadow-xs">
        <div className="flex items-start justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1e293b] text-xs font-semibold mb-3">
              <Megaphone className="w-3.5 h-3.5 text-[#8b5cf6]" />
              <span>{config.eyebrow}</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">{config.title}</h2>
            <p className="text-sm text-[#cbd5e1] mt-3 leading-relaxed">{config.description}</p>
          </div>
          <div
            className="hidden md:flex w-14 h-14 rounded-2xl items-center justify-center text-[#0f172a] shrink-0"
            style={{ backgroundColor: config.accent }}
          >
            {config.icon}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-[#e2e8f0] bg-[#f1f5f9] px-4 py-3 flex items-center gap-3">
        <ShieldCheck className="w-4 h-4 text-[#8b5cf6] shrink-0" />
        <p className="text-xs text-[#64748b]">
          <strong className="text-[#0f172a]">Foundation mode.</strong> Workflow boundaries are visible; external platform actions remain disabled until official credentials and permissions are connected.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {config.cards.map((card) => (
          <Card key={card.title} className="p-5 bg-[#ffffff]">
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="w-9 h-9 rounded-xl bg-[#f8fafc] flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4 text-[#0f172a]" />
              </div>
              <span className="px-2 py-1 rounded-full bg-[#f1f5f9] text-[9px] font-black uppercase tracking-wider text-[#64748b]">
                {card.status}
              </span>
            </div>
            <h3 className="font-bold text-[#0f172a]">{card.title}</h3>
            <p className="text-xs text-[#64748b] mt-2 leading-relaxed">{card.description}</p>
          </Card>
        ))}
      </div>

      <Card className="p-8 bg-[#ffffff] text-center">
        <div className="w-10 h-10 rounded-xl bg-[#f8fafc] text-[#94a3b8] flex items-center justify-center mx-auto mb-3">
          {config.icon}
        </div>
        <p className="font-bold text-[#0f172a]">No operational data yet</p>
        <p className="text-xs text-[#64748b] mt-1 max-w-lg mx-auto">
          This workspace will populate automatically when its provider integration and worker workflow are activated.
        </p>
      </Card>
    </div>
  );
};
