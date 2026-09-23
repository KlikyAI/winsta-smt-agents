import React, { useState } from 'react';
import { Settings, Save } from 'lucide-react';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { useToast } from '../../../context/ToastContext';

export const SettingsTab: React.FC = () => {
  const { addToast } = useToast();

  const [systemConfig, setSystemConfig] = useState(() => {
    const saved = localStorage.getItem('winsta_system_config');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // use default
      }
    }
    return {
      defaultCountry: 'KW',
      minScoreThreshold: 0.70,
      autoApproveAboveScore: 0.92,
      enableAutoWorkflow: true,
      maxTokensPerRun: 2048,
      rateLimitPerMinute: 60,
      cacheTtlSeconds: 3600,
      webhookUrl: 'https://api.winsta.ai/webhooks/trends-ready',
    };
  });

  const handleSaveSystemConfig = () => {
    localStorage.setItem('winsta_system_config', JSON.stringify(systemConfig));
    addToast('success', 'System Settings Saved', 'Operational thresholds and workspace configurations saved.');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-slate-100 text-slate-800 flex items-center justify-center">
              <Settings className="w-4 h-4" />
            </span>
            <h3 className="text-lg font-bold tracking-tight text-slate-900">
              System Settings & Automation Limits
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure operational parameters, default regional discovery, quality thresholds, and rate limits.
          </p>
        </div>
        <Button variant="lime" size="sm" onClick={handleSaveSystemConfig} leftIcon={<Save className="w-3.5 h-3.5" />}>
          Save Settings
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Discovery & Quality Controls */}
        <Card className="p-6 bg-white border border-slate-200 space-y-4">
          <h4 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Trend Discovery & Quality Gates</h4>
          
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Default Discovery Country</label>
            <select
              value={systemConfig.defaultCountry}
              onChange={(e) => setSystemConfig({ ...systemConfig, defaultCountry: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
            >
              <option value="KW">KW • Kuwait (Primary Target)</option>
              <option value="SA">SA • Saudi Arabia</option>
              <option value="AE">AE • United Arab Emirates</option>
              <option value="US">US • United States</option>
              <option value="GLOBAL">GLOBAL • Worldwide</option>
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">Minimum Scoring Threshold</label>
              <span className="text-xs font-bold text-purple-700">{systemConfig.minScoreThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={systemConfig.minScoreThreshold}
              onChange={(e) => setSystemConfig({ ...systemConfig, minScoreThreshold: parseFloat(e.target.value) })}
              className="w-full accent-[#8b5cf6]"
            />
            <p className="text-[11px] text-slate-500 mt-1">Candidates below this score are automatically filtered out before 6-modality prompt synthesis.</p>
          </div>

          <div className="pt-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={systemConfig.enableAutoWorkflow}
                onChange={(e) => setSystemConfig({ ...systemConfig, enableAutoWorkflow: e.target.checked })}
                className="w-4 h-4 rounded text-[#8b5cf6] accent-[#8b5cf6]"
              />
              <div>
                <span className="text-xs font-bold text-slate-900 block">Enable LangGraph Autonomous Pipeline</span>
                <span className="text-[11px] text-slate-500">Automatically run deduplication, scoring, enrichment, and prompt synthesis on discovery.</span>
              </div>
            </label>
          </div>
        </Card>

        {/* Performance & Security Limits */}
        <Card className="p-6 bg-white border border-slate-200 space-y-4">
          <h4 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Performance & Caching Limits</h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Max AI Tokens / Call</label>
              <input
                type="number"
                value={systemConfig.maxTokensPerRun}
                onChange={(e) => setSystemConfig({ ...systemConfig, maxTokensPerRun: parseInt(e.target.value) || 2048 })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Rate Limit (req/min)</label>
              <input
                type="number"
                value={systemConfig.rateLimitPerMinute}
                onChange={(e) => setSystemConfig({ ...systemConfig, rateLimitPerMinute: parseInt(e.target.value) || 60 })}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Redis Runtime Cache TTL (Seconds)</label>
            <input
              type="number"
              value={systemConfig.cacheTtlSeconds}
              onChange={(e) => setSystemConfig({ ...systemConfig, cacheTtlSeconds: parseInt(e.target.value) || 3600 })}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Outbound Webhook URL</label>
            <input
              type="url"
              value={systemConfig.webhookUrl}
              onChange={(e) => setSystemConfig({ ...systemConfig, webhookUrl: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-xs text-slate-900 font-mono outline-none"
            />
          </div>
        </Card>
      </div>
    </div>
  );
};

