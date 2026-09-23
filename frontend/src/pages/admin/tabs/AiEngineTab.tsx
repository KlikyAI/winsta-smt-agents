import React, { useState, useEffect } from 'react';
import {
  Cpu,
  RefreshCw,
  CheckCircle2,
  KeyRound,
  Save,
  Play,
} from 'lucide-react';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { AIProviderLogo } from '../../../components/common/AIProviderLogo';
import { aiApi, type AIProviderStatus, type AIRuntimeSettings } from '../../../api/ai';
import { useToast } from '../../../context/ToastContext';

export const AiEngineTab: React.FC = () => {
  const { addToast } = useToast();

  const [providers, setProviders] = useState<AIProviderStatus[]>([]);
  const [runtimeSettings, setRuntimeSettings] = useState<AIRuntimeSettings | null>(null);
  const [isLoadingProviders, setIsLoadingProviders] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<string>('deepseek');
  const [selectedModel, setSelectedModel] = useState<string>('deepseek-chat');
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  // LLM Sandbox Testing state
  const [testPrompt, setTestPrompt] = useState('Explain how AI trends drive creative marketing growth in 2 sentences.');
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    fetchProvidersAndSettings();
  }, []);

  const fetchProvidersAndSettings = async () => {
    setIsLoadingProviders(true);
    try {
      const [provRes, setRes] = await Promise.all([
        aiApi.getProviders(),
        aiApi.getSettings(),
      ]);
      setProviders(provRes.data || []);
      if (setRes.data) {
        setRuntimeSettings(setRes.data);
        setSelectedProvider(setRes.data.ai_provider || 'deepseek');
        setSelectedModel(setRes.data.ai_model || 'deepseek-chat');
      }
    } catch {
      // ignore
    } finally {
      setIsLoadingProviders(false);
    }
  };

  const handleProviderSelect = (providerName: string) => {
    setSelectedProvider(providerName);
    const prov = providers.find((p) => p.provider === providerName);
    if (prov && prov.models.length > 0) {
      setSelectedModel(prov.models[0].id);
    }
    setApiKeyInput('');
  };

  const handleSaveRuntimeSettings = async () => {
    setIsSavingSettings(true);
    try {
      const payload: any = {
        ai_provider: selectedProvider,
        ai_model: selectedModel,
      };
      if (apiKeyInput.trim()) {
        const keyField = `${selectedProvider}_api_key`;
        payload[keyField] = apiKeyInput.trim();
      }

      const res = await aiApi.updateSettings(payload);
      setRuntimeSettings(res.data);
      setApiKeyInput('');
      await fetchProvidersAndSettings();
      addToast(
        'success',
        'AI Configuration Applied',
        `Active model switched to ${selectedProvider.toUpperCase()} (${selectedModel}) instantly without restart!`
      );
    } catch (err: any) {
      addToast('error', 'Failed to update AI settings', err.message);
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleTestLLM = async () => {
    if (!testPrompt.trim()) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await aiApi.testCompletion({
        prompt: testPrompt,
        provider: selectedProvider,
        model: selectedModel,
      });
      setTestResult(res.data);
      addToast('success', 'LLM Test Completed', `Generated via ${res.data.provider} (${res.data.latency_ms}ms)`);
    } catch (err: any) {
      addToast('error', 'LLM Test Failed', err.message || 'Check provider API key');
    } finally {
      setIsTesting(false);
    }
  };

  const activeProviderData = providers.find((p) => p.provider === selectedProvider);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-7 h-7 rounded-lg bg-[#0f172a] text-[#a78bfa] flex items-center justify-center">
              <Cpu className="w-4 h-4" />
            </span>
            <h3 className="text-lg font-bold tracking-tight text-slate-900">
              AI Multi-Provider Engine
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Switch active LLMs and update API keys dynamically directly from the UI without modifying <code className="text-purple-700">.env</code>.
          </p>
        </div>
        <Button variant="light" size="sm" onClick={fetchProvidersAndSettings} isLoading={isLoadingProviders} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          Refresh Status
        </Button>
      </div>

      {/* Provider Cards Catalog */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {providers.map((p) => {
          const isSelected = selectedProvider === p.provider;
          const isCurrentActive = runtimeSettings?.ai_provider === p.provider;

          return (
            <Card
              key={p.provider}
              onClick={() => handleProviderSelect(p.provider)}
              className={`p-4 cursor-pointer transition-all border ${
                isSelected
                  ? 'bg-white border-[#8b5cf6] shadow-md ring-2 ring-[#8b5cf6]'
                  : isCurrentActive
                  ? 'bg-purple-50/50 border-purple-300'
                  : 'bg-white border-slate-200 hover:border-slate-400'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <AIProviderLogo provider={p.provider} size="md" />
                  <div>
                    <h4 className="font-bold text-slate-900 capitalize text-xs">{p.provider}</h4>
                    <span className="text-[10px] text-slate-500 font-mono block truncate max-w-[110px]">
                      {p.default_model}
                    </span>
                  </div>
                </div>

                {isCurrentActive && (
                  <span className="px-2 py-0.5 rounded-full bg-[#0f172a] text-[#a78bfa] text-[9px] font-bold uppercase">
                    Active
                  </span>
                )}
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-400 text-[10px]">
                  {p.models.length} Models
                </span>
                <div>
                  {p.is_configured ? (
                    <span className="text-emerald-600 font-bold text-[10px] flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Ready
                    </span>
                  ) : (
                    <span className="text-amber-600 font-medium text-[10px] flex items-center gap-1">
                      <KeyRound className="w-3 h-3" /> Key Needed
                    </span>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Dynamic Model & API Key Configuration Box */}
      <Card className="p-6 bg-white border border-slate-200 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <AIProviderLogo provider={selectedProvider} size="md" />
            <div>
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                Configure Active Engine: <span className="capitalize text-[#8b5cf6]">{selectedProvider}</span>
              </h4>
              <p className="text-xs text-slate-500">
                Currently running in production across Discovery Runs, 6-Modality Synthesis, and Social Studio.
              </p>
            </div>
          </div>

          <Button
            variant="lime"
            size="sm"
            onClick={handleSaveRuntimeSettings}
            isLoading={isSavingSettings}
            leftIcon={<Save className="w-4 h-4" />}
          >
            Save & Apply Dynamic Setting
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Select Active Model */}
          <div>
            <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-[#8b5cf6]" /> Target Model for {selectedProvider.toUpperCase()}
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-white border border-slate-300 focus:border-[#8b5cf6] rounded-xl p-2.5 text-xs text-slate-900 outline-none font-medium shadow-xs"
            >
              {activeProviderData?.models && activeProviderData.models.length > 0 ? (
                activeProviderData.models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.id})
                  </option>
                ))
              ) : (
                <option value={selectedModel}>{selectedModel}</option>
              )}
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              Selected model will be used immediately for subsequent trend discoveries and prompt synthesis.
            </p>
          </div>

          {/* Optional API Key Input */}
          <div>
            <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <KeyRound className="w-3.5 h-3.5 text-[#8b5cf6]" /> Update {selectedProvider.toUpperCase()} API Key (Optional)
            </label>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder={activeProviderData?.is_configured ? '•••••••••••••••••••••••• (Configured)' : 'Enter API Key (e.g. sk-...)'}
              className="w-full bg-white border border-slate-300 focus:border-[#8b5cf6] rounded-xl p-2.5 text-xs text-slate-900 font-mono outline-none shadow-xs"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Leave empty to keep existing key. New key is stored securely in runtime memory and Redis.
            </p>
          </div>
        </div>
      </Card>

      {/* Interactive LLM Testing Sandbox */}
      <Card className="p-6 bg-white border border-slate-200 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AIProviderLogo provider={selectedProvider} size="sm" />
            <h4 className="text-sm font-bold text-slate-900">
              LLM Sandbox Test ({selectedProvider.toUpperCase()} • {selectedModel})
            </h4>
          </div>
          <span className="text-xs text-slate-500">Test live completion directly via API</span>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            placeholder="Enter a prompt to test..."
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-xs text-slate-900 outline-none focus:border-[#8b5cf6]"
          />
          <Button
            variant="primary"
            size="sm"
            onClick={handleTestLLM}
            isLoading={isTesting}
            leftIcon={<Play className="w-3.5 h-3.5 fill-[#a78bfa] text-[#a78bfa]" />}
          >
            Run Completion
          </Button>
        </div>

        {testResult && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 animate-fade-in">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Model: <strong className="text-slate-900">{testResult.model}</strong> ({testResult.provider})</span>
              <span>Latency: <strong className="text-purple-700">{testResult.latency_ms}ms</strong></span>
            </div>
            <p className="text-xs text-slate-800 font-medium leading-relaxed bg-white p-3 rounded-lg border border-slate-200">
              {testResult.content}
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

