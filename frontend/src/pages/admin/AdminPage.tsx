import React from 'react';
import {
  Bot,
  Building2,
  Palette,
  Settings,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AiEngineTab, UsersTab, BrandKitTab, SettingsTab } from './tabs';

export type AdminTab = 'ai_engine' | 'users' | 'brand_kit' | 'settings';

interface AdminPageProps {
  section?: AdminTab;
}

const tabToPath: Record<AdminTab, string> = {
  ai_engine: '/admin/ai-engine',
  users: '/admin/users',
  brand_kit: '/admin/brand-kit',
  settings: '/admin/settings',
};

export const AdminPage: React.FC<AdminPageProps> = ({ section }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const getActiveTabFromLocation = (): AdminTab => {
    if (section) return section;
    const path = location.pathname;
    if (path.includes('/admin/users')) return 'users';
    if (path.includes('/admin/brand-kit')) return 'brand_kit';
    if (path.includes('/admin/settings')) return 'settings';
    return 'ai_engine';
  };

  const activeTab = getActiveTabFromLocation();

  const handleTabChange = (tab: AdminTab) => {
    navigate(tabToPath[tab]);
  };

  const adminModules = [
    {
      id: 'ai_engine' as AdminTab,
      title: 'AI Multi-Provider Engine',
      description: 'Dynamic real-time router supporting DeepSeek, OpenAI, Claude, Gemini, Groq, Ollama, and OpenRouter.',
      icon: <Bot className="w-5 h-5" />,
      badgeColor: 'bg-purple-100 text-purple-800 border-purple-200',
    },
    {
      id: 'users' as AdminTab,
      title: 'Users & Roles',
      description: 'Manage internal users, access levels, and role-based permissions across Winsta AI Studio.',
      icon: <Users className="w-5 h-5" />,
      badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
    },
    {
      id: 'brand_kit' as AdminTab,
      title: 'Brand Kit',
      description: 'Centralize Winsta logos, colors, fonts, tone, and content guidelines for social generation.',
      icon: <Palette className="w-5 h-5" />,
      badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    },
    {
      id: 'settings' as AdminTab,
      title: 'System Settings',
      description: 'Control organization defaults, approval policies, integrations, and operational limits.',
      icon: <Settings className="w-5 h-5" />,
      badgeColor: 'bg-slate-100 text-slate-800 border-slate-200',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="rounded-2xl p-8 bg-[#ffffff] border border-slate-200 shadow-xs">
        <div className="flex items-start justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 border border-purple-200 text-xs font-semibold text-purple-700 mb-3">
              <ShieldCheck className="w-3.5 h-3.5 text-[#8b5cf6]" />
              <span>Administration Control Center</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
              Winsta AI Admin Center
            </h2>
            <p className="text-sm text-slate-600 mt-3 leading-relaxed">
              Centralized platform governance for Prompt Trends and Omnichannel Social Studio. Manage dynamic multi-provider LLMs, internal team access, brand presets, and system thresholds.
            </p>
          </div>
          <div className="hidden md:flex w-14 h-14 rounded-2xl bg-[#0f172a] text-[#a78bfa] items-center justify-center shadow-xs">
            <Building2 className="w-7 h-7" />
          </div>
        </div>

        {/* Module Navigation Tabs */}
        <div className="flex flex-wrap gap-2 mt-8 pt-6 border-t border-slate-100">
          {adminModules.map((mod) => {
            const isActive = activeTab === mod.id;
            return (
              <button
                key={mod.id}
                onClick={() => handleTabChange(mod.id)}
                className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl font-bold text-xs transition-all ${
                  isActive
                    ? 'bg-[#0f172a] text-white shadow-md'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200'
                }`}
              >
                <span className={isActive ? 'text-[#a78bfa]' : 'text-slate-500'}>
                  {mod.icon}
                </span>
                <span>{mod.title}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Render Active Tab Component */}
      {activeTab === 'ai_engine' && <AiEngineTab />}
      {activeTab === 'users' && <UsersTab />}
      {activeTab === 'brand_kit' && <BrandKitTab />}
      {activeTab === 'settings' && <SettingsTab />}
    </div>
  );
};
