import React, { useState, useEffect } from 'react';
import { Play, Activity, Shield, LogOut, Plus, ChevronDown, Building2 } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../common/Button';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { LANGUAGES } from '../../i18n/translations';
import { systemApi } from '../../api/system';
import { useToast } from '../../context/ToastContext';

interface HeaderProps {
  onTriggerRun: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onTriggerRun }) => {
  const { user, logout, workspaces, selectedWorkspaceId, selectWorkspace, createWorkspace } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const { addToast } = useToast();
  const location = useLocation();
  const navigate = useNavigate();
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);
  const [isLangOpen, setIsLangOpen] = useState(false);
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [isCreateWorkspaceOpen, setIsCreateWorkspaceOpen] = useState(false);
  const [workspaceName, setWorkspaceName] = useState('');
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const isSocialWorkspace = location.pathname.startsWith('/social');
  const isAdminWorkspace = location.pathname.startsWith('/admin');

  const currentLangObj = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];
  const selectedWorkspace = workspaces.find((workspace) => workspace.id === selectedWorkspaceId) || workspaces[0];

  const handleWorkspaceSelect = (workspaceId: string) => {
    selectWorkspace(workspaceId);
    setIsWorkspaceOpen(false);
    window.location.reload();
  };

  const handleCreateWorkspace = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!workspaceName.trim()) return;
    setIsCreatingWorkspace(true);
    try {
      await createWorkspace(workspaceName.trim());
      setWorkspaceName('');
      setIsCreateWorkspaceOpen(false);
      setIsWorkspaceOpen(false);
      addToast('success', 'Workspace created', 'The new workspace is now active.');
      window.location.reload();
    } catch (error: any) {
      addToast('error', 'Unable to create workspace', error?.message || 'Please try another name.');
    } finally {
      setIsCreatingWorkspace(false);
    }
  };

  const handlePrimaryAction = () => {
    if (isSocialWorkspace) {
      navigate('/social');
      requestAnimationFrame(() => {
        document.getElementById('social-brief-form')?.scrollIntoView({ behavior: 'smooth' });
      });
      return;
    }
    onTriggerRun();
  };

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = (await systemApi.getReadiness()) as any;
        const status = res?.status || res?.data?.status;
        setIsBackendHealthy(status === 'ready' || status === 'ok');
      } catch {
        setIsBackendHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-18 bg-[#ffffff]/95 border-b border-slate-200 backdrop-blur-md px-6 md:px-8 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* System status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-slate-200 text-xs font-semibold shadow-xs">
          <Activity
            className={`w-3.5 h-3.5 ${
              isBackendHealthy === true
                ? 'text-emerald-500'
                : isBackendHealthy === false
                ? 'text-rose-500'
                : 'text-slate-400'
            }`}
          />
          <span className="text-slate-500">
            {t('nav.connected')}:{' '}
            <strong className="text-slate-900">
              {isBackendHealthy === true ? 'Ready' : isBackendHealthy === false ? 'Offline' : 'Connecting...'}
            </strong>
          </span>
        </div>
      </div>

      {/* Actions, Language Switcher & User Profile */}
      <div className="flex items-center gap-3 md:gap-4">
        {!isAdminWorkspace && (
          <Button
            variant="primary"
            size="sm"
            onClick={handlePrimaryAction}
            leftIcon={isSocialWorkspace
              ? <Plus className="w-3.5 h-3.5 text-[#a78bfa]" />
              : <Play className="w-3.5 h-3.5 fill-[#a78bfa] text-[#a78bfa]" />}
          >
            {isSocialWorkspace ? 'New Social Brief' : t('hero.start_run')}
          </Button>
        )}

        {/* Workspace switcher */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsWorkspaceOpen((open) => !open)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-[#8b5cf6] text-xs font-bold text-slate-800 transition-colors shadow-xs cursor-pointer max-w-[190px]"
            title="Switch workspace"
          >
            <Building2 className="w-3.5 h-3.5 text-[#8b5cf6] shrink-0" />
            <span className="truncate hidden sm:inline">{selectedWorkspace?.name || 'Workspace'}</span>
            <ChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
          </button>

          {isWorkspaceOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-slate-200 shadow-xl p-2 z-50 animate-fade-in">
              <p className="px-3 py-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Workspaces</p>
              {workspaces.map((workspace) => (
                <button
                  key={workspace.id}
                  type="button"
                  onClick={() => handleWorkspaceSelect(workspace.id)}
                  className={`w-full px-3 py-2 rounded-xl text-left text-xs font-semibold flex items-center justify-between ${workspace.id === selectedWorkspace?.id ? 'bg-purple-50 text-purple-700' : 'text-slate-700 hover:bg-slate-50'}`}
                >
                  <span className="truncate">{workspace.name}</span>
                  <span className="ml-2 text-[10px] text-slate-400 capitalize">{workspace.role}</span>
                </button>
              ))}
              <div className="border-t border-slate-100 mt-2 pt-2">
                {!isCreateWorkspaceOpen ? (
                  <button type="button" onClick={() => setIsCreateWorkspaceOpen(true)} className="w-full px-3 py-2 rounded-xl text-left text-xs font-bold text-[#7c3aed] hover:bg-purple-50">+ Create workspace</button>
                ) : (
                  <form onSubmit={handleCreateWorkspace} className="space-y-2 px-1">
                    <input autoFocus required value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} placeholder="Workspace name" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs outline-none focus:border-[#8b5cf6]" />
                    <div className="flex gap-2">
                      <button type="submit" disabled={isCreatingWorkspace} className="flex-1 rounded-lg bg-[#0f172a] text-white px-2 py-2 text-xs font-bold disabled:opacity-50">{isCreatingWorkspace ? 'Creating…' : 'Create'}</button>
                      <button type="button" onClick={() => setIsCreateWorkspaceOpen(false)} className="rounded-lg border border-slate-200 px-2 py-2 text-xs font-bold text-slate-600">Cancel</button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 3-Language Selector Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsLangOpen(!isLangOpen)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-[#8b5cf6] text-xs font-bold text-slate-800 transition-colors shadow-xs cursor-pointer"
            title="Switch Language (English / العربية / Bahasa Indonesia)"
          >
            <span>{currentLangObj.flag}</span>
            <span className="hidden sm:inline">{currentLangObj.nativeLabel}</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {isLangOpen && (
            <div className="absolute right-0 mt-2 w-44 rounded-2xl bg-white border border-slate-200 shadow-xl py-1.5 z-50 animate-fade-in">
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 mb-1">
                {t('lang.select')}
              </div>
              {LANGUAGES.map((item) => (
                <button
                  key={item.code}
                  type="button"
                  onClick={() => {
                    setLanguage(item.code);
                    setIsLangOpen(false);
                  }}
                  className={`w-full px-3 py-2 text-left text-xs font-semibold flex items-center justify-between transition-colors cursor-pointer ${
                    language === item.code
                      ? 'bg-purple-50 text-purple-700 font-bold'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span>{item.flag}</span>
                    <span>{item.nativeLabel}</span>
                  </span>
                  {language === item.code && (
                    <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6]" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Authenticated user */}
        <div className="flex items-center gap-2 border-l border-slate-200 pl-3 md:pl-4">
          <div className="hidden lg:flex items-center gap-1.5 bg-white border border-slate-200 rounded-full px-3 py-1 shadow-xs">
            <Shield className="w-3.5 h-3.5 text-[#8b5cf6]" />
            <span className="text-xs font-bold capitalize text-slate-900">{(user?.role || 'viewer').replace('_', ' ')}</span>
          </div>

          <div className="flex items-center gap-2 bg-slate-100 border border-slate-200 rounded-full pl-2 pr-3 py-1">
            <div className="w-6 h-6 rounded-full bg-[#0f172a] text-[#a78bfa] flex items-center justify-center font-bold text-[10px]">
              {user?.full_name.charAt(0) || 'A'}
            </div>
            <span className="text-xs font-bold text-slate-900 hidden sm:inline">{user?.full_name || 'Admin'}</span>
          </div>

          <button
            onClick={logout}
            className="p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-full transition-colors cursor-pointer border border-slate-200"
            title={t('nav.logout')}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
