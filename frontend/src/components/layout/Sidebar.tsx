import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  BarChart3,
  Bot,
  CalendarDays,
  ClipboardCheck,
  DollarSign,
  Flame,
  Link2,
  LayoutDashboard,
  Megaphone,
  Palette,
  PlayCircle,
  Settings,
  Share2,
  Sliders,
  Users,
} from 'lucide-react';
import { usePermissions } from '../../hooks/usePermissions';
import { useLanguage } from '../../context/LanguageContext';
import { WinstaLogo } from '../common/WinstaLogo';

interface NavigationItem {
  path: string;
  labelKey: string;
  defaultLabel: string;
  icon: React.ReactNode;
  exact?: boolean;
}

interface NavigationGroup {
  labelKey?: string;
  defaultLabel?: string;
  items: NavigationItem[];
}

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const { isAdmin } = usePermissions();
  const { t } = useLanguage();
  const currentPath = location.pathname;

  const navigationGroups: NavigationGroup[] = [
    {
      items: [
        {
          path: '/',
          labelKey: 'nav.dashboard',
          defaultLabel: 'Dashboard',
          icon: <LayoutDashboard className="w-4 h-4" />,
          exact: true,
        },
      ],
    },
    {
      labelKey: 'nav.group.trends',
      defaultLabel: 'Prompt Trends',
      items: [
        { path: '/trends', labelKey: 'nav.trends', defaultLabel: 'Trends Explorer', icon: <Flame className="w-4 h-4" /> },
        { path: '/runs', labelKey: 'nav.runs', defaultLabel: 'Discovery Runs', icon: <PlayCircle className="w-4 h-4" /> },
        { path: '/sources', labelKey: 'nav.sources', defaultLabel: 'Platform Sources', icon: <Share2 className="w-4 h-4" /> },
        { path: '/scoring', labelKey: 'nav.scoring', defaultLabel: 'Scoring Studio', icon: <Sliders className="w-4 h-4" /> },
      ],
    },
    {
      labelKey: 'nav.group.social',
      defaultLabel: 'Social Media AI',
      items: [
        { path: '/social', labelKey: 'nav.social', defaultLabel: 'Social Studio', icon: <Megaphone className="w-4 h-4" />, exact: true },
        { path: '/social/calendar', labelKey: 'nav.social.calendar', defaultLabel: 'Calendar & Publishing', icon: <CalendarDays className="w-4 h-4" /> },
        { path: '/social/approvals', labelKey: 'nav.social.approvals', defaultLabel: 'Approvals', icon: <ClipboardCheck className="w-4 h-4" /> },
        { path: '/social/accounts', labelKey: 'nav.social.accounts', defaultLabel: 'Social Accounts', icon: <Link2 className="w-4 h-4" /> },
        { path: '/social/analytics', labelKey: 'nav.social.analytics', defaultLabel: 'Analytics', icon: <BarChart3 className="w-4 h-4" /> },
        { path: '/social/campaigns', labelKey: 'nav.social.campaigns', defaultLabel: 'Paid Campaigns', icon: <DollarSign className="w-4 h-4" /> },
      ],
    },
  ];

  if (isAdmin) {
    navigationGroups.push({
      labelKey: 'nav.group.admin',
      defaultLabel: 'Administration',
      items: [
        { path: '/admin/ai-engine', labelKey: 'nav.admin.ai', defaultLabel: 'AI Engine & LLMs', icon: <Bot className="w-4 h-4" /> },
        { path: '/admin/users', labelKey: 'nav.admin.users', defaultLabel: 'Users & Roles', icon: <Users className="w-4 h-4" /> },
        { path: '/admin/brand-kit', labelKey: 'nav.admin.brand', defaultLabel: 'Brand Kit', icon: <Palette className="w-4 h-4" /> },
        { path: '/admin/settings', labelKey: 'nav.admin.settings', defaultLabel: 'System Settings', icon: <Settings className="w-4 h-4" /> },
      ],
    });
  }

  const isActive = (item: NavigationItem) => {
    if (item.path === '/') {
      return currentPath === '/' || currentPath === '/dashboard';
    }
    return item.exact ? currentPath === item.path : currentPath.startsWith(item.path);
  };

  return (
    <aside className="w-64 bg-[#ffffff] border-r border-slate-200 flex flex-col justify-between p-4 shrink-0 h-screen sticky top-0 overflow-y-auto custom-scrollbar">
      <div>
        <Link to="/" className="flex items-center px-2 py-4 mb-5 group cursor-pointer">
          <WinstaLogo size="md" showText={true} />
        </Link>

        <nav className="space-y-5">
          {navigationGroups.map((group, groupIndex) => (
            <div key={group.labelKey || `primary-${groupIndex}`}>
              {group.defaultLabel && (
                <p className="px-3.5 mb-2 text-[9px] font-black uppercase tracking-[0.16em] text-slate-400">
                  {group.labelKey ? t(group.labelKey, group.defaultLabel) : group.defaultLabel}
                </p>
              )}
              <div className="space-y-1">
                {group.items.map((item) => {
                  const active = isActive(item);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-full text-xs font-bold transition-all duration-150 cursor-pointer ${
                        active
                          ? 'bg-[#0f172a] text-[#ffffff] shadow-[3px_3px_0px_#0f172a] border border-[#0f172a]'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
                      }`}
                    >
                      <div className={active ? 'text-[#a78bfa]' : 'text-slate-400'}>{item.icon}</div>
                      <span>{t(item.labelKey, item.defaultLabel)}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      <div className="pt-4 mt-6 border-t border-slate-200 px-1">
        <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 mb-3">
          <p className="text-[11px] font-bold text-slate-900">{t('nav.platform.unified', 'Unified Winsta Platform')}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="w-2 h-2 rounded-full bg-[#8b5cf6]" />
            <span className="text-[10px] text-slate-800 font-semibold">{t('nav.platform.sub', 'Trends • Social • Admin')}</span>
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 text-[10px] text-slate-500 font-medium">
          <Link to="/privacy" className="hover:text-purple-600 transition-colors">
            Privacy
          </Link>
          <span>•</span>
          <Link to="/terms" className="hover:text-purple-600 transition-colors">
            Terms
          </Link>
          <span>•</span>
          <Link to="/data-deletion" className="hover:text-purple-600 transition-colors">
            Data Deletion
          </Link>
        </div>
      </div>
    </aside>
  );
};
