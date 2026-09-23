import React, { useState, useEffect } from 'react';
import { ShieldCheck, ExternalLink, Eye, EyeOff, Save } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { useToast } from '../../context/ToastContext';
import { trendSourcesApi } from '../../api/trendSources';
import type { TrendSource } from '../../types/trendSource';

interface ConfigureSourceModalProps {
  source: TrendSource | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ConfigureSourceModal: React.FC<ConfigureSourceModalProps> = ({
  source,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { addToast } = useToast();
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [showSecret, setShowSecret] = useState<Record<string, boolean>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (source) {
      setFormData(source.configuration || {});
    }
  }, [source]);

  if (!source) return null;

  const toggleSecret = (field: string) => {
    setShowSecret((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const handleChange = (field: string, val: string) => {
    setFormData((prev) => ({ ...prev, [field]: val }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await trendSourcesApi.updateSource(source.id, {
        configuration: formData,
      });
      addToast('success', 'Credentials Saved', `${source.name} credentials have been updated and stored securely.`);
      onSuccess();
      onClose();
    } catch (err: any) {
      addToast('error', 'Failed to Save', err.message || 'Error updating source configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const renderPlatformForm = () => {
    switch (source.platform) {
      case 'instagram':
        return (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] text-xs text-[#64748b] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#0f172a]">Meta Developer Credentials</span>
                <a
                  href="https://developers.facebook.com/apps/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#8b5cf6] hover:underline flex items-center gap-1 font-bold text-[11px]"
                >
                  developers.facebook.com <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p>Enter your Meta App ID and App Secret. The system will automatically exchange and refresh active access tokens.</p>
            </div>

            <div>
              <Input
                label="Meta App ID (Client ID)"
                placeholder="e.g. 19823487123984"
                value={formData.client_id || formData.app_id || ''}
                onChange={(e) => handleChange('client_id', e.target.value)}
              />
              <span className="text-[11px] text-[#64748b] mt-1 block">Found in Meta App Dashboard &gt; Basic Settings</span>
            </div>

            <div className="relative">
              <Input
                label="Meta App Secret (Client Secret)"
                type={showSecret.client_secret ? 'text' : 'password'}
                placeholder="e.g. 9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c"
                value={formData.client_secret || formData.app_secret || ''}
                onChange={(e) => handleChange('client_secret', e.target.value)}
              />
              <button
                type="button"
                onClick={() => toggleSecret('client_secret')}
                className="absolute right-3 top-9 text-[#94a3b8] hover:text-[#0f172a]"
              >
                {showSecret.client_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
              <span className="text-[11px] text-[#64748b] mt-1 block">Kept encrypted in PostgreSQL and never exposed in frontend API</span>
            </div>

            <div>
              <Input
                label="Direct Access Token (Optional Fallback)"
                placeholder="IGQVJ..."
                value={formData.access_token || ''}
                onChange={(e) => handleChange('access_token', e.target.value)}
              />
              <span className="text-[11px] text-[#64748b] mt-1 block">Optional: Leave blank if using Meta App ID &amp; Secret above</span>
            </div>
          </div>
        );

      case 'tiktok':
        return (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] text-xs text-[#64748b] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#0f172a]">TikTok for Developers Credentials</span>
                <a
                  href="https://developers.tiktok.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#8b5cf6] hover:underline flex items-center gap-1 font-bold text-[11px]"
                >
                  developers.tiktok.com <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p>Uses OAuth 2.0 Client Credentials Grant to scrape trending sounds and video topics.</p>
            </div>

            <Input
              label="TikTok Client Key"
              placeholder="e.g. aw9z8y7x6w5v4u3t"
              value={formData.client_key || formData.client_id || ''}
              onChange={(e) => handleChange('client_key', e.target.value)}
            />

            <div className="relative">
              <Input
                label="TikTok Client Secret"
                type={showSecret.client_secret ? 'text' : 'password'}
                placeholder="e.g. 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d"
                value={formData.client_secret || ''}
                onChange={(e) => handleChange('client_secret', e.target.value)}
              />
              <button
                type="button"
                onClick={() => toggleSecret('client_secret')}
                className="absolute right-3 top-9 text-[#94a3b8] hover:text-[#0f172a]"
              >
                {showSecret.client_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Input
              label="Direct Access Token (Optional Fallback)"
              placeholder="act.example..."
              value={formData.access_token || ''}
              onChange={(e) => handleChange('access_token', e.target.value)}
            />
          </div>
        );

      case 'x':
        return (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] text-xs text-[#64748b] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#0f172a]">X (Twitter API v2) Credentials</span>
                <a
                  href="https://developer.x.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#8b5cf6] hover:underline flex items-center gap-1 font-bold text-[11px]"
                >
                  developer.x.com <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p>Supports OAuth 2.0 App Credentials or API Key &amp; Secret for Twitter API v2 endpoints.</p>
            </div>

            <Input
              label="X Client ID (or API Key)"
              placeholder="e.g. VXZQ..."
              value={formData.client_id || formData.api_key || ''}
              onChange={(e) => handleChange('client_id', e.target.value)}
            />

            <div className="relative">
              <Input
                label="X Client Secret (or API Secret)"
                type={showSecret.client_secret ? 'text' : 'password'}
                placeholder="e.g. 8kL9..."
                value={formData.client_secret || formData.api_secret || ''}
                onChange={(e) => handleChange('client_secret', e.target.value)}
              />
              <button
                type="button"
                onClick={() => toggleSecret('client_secret')}
                className="absolute right-3 top-9 text-[#94a3b8] hover:text-[#0f172a]"
              >
                {showSecret.client_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Input
              label="Direct Bearer Token (Optional Fallback)"
              placeholder="AAAAAAAAAAAAAAAAAAAA..."
              value={formData.bearer_token || ''}
              onChange={(e) => handleChange('bearer_token', e.target.value)}
            />
          </div>
        );

      case 'linkedin':
        return (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] text-xs text-[#64748b] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#0f172a]">LinkedIn Developer Credentials</span>
                <a
                  href="https://www.linkedin.com/developers/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#8b5cf6] hover:underline flex items-center gap-1 font-bold text-[11px]"
                >
                  linkedin.com/developers <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p>Collects B2B visual branding trends, viral carousel posts, and executive thought leadership.</p>
            </div>

            <Input
              label="LinkedIn Client ID"
              placeholder="e.g. 86nbtl9sjrjv28"
              value={formData.client_id || ''}
              onChange={(e) => handleChange('client_id', e.target.value)}
            />

            <div className="relative">
              <Input
                label="LinkedIn Client Secret"
                type={showSecret.client_secret ? 'text' : 'password'}
                placeholder="e.g. WPL_AP1..."
                value={formData.client_secret || ''}
                onChange={(e) => handleChange('client_secret', e.target.value)}
              />
              <button
                type="button"
                onClick={() => toggleSecret('client_secret')}
                className="absolute right-3 top-9 text-[#94a3b8] hover:text-[#0f172a]"
              >
                {showSecret.client_secret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <Input
              label="OAuth Scopes"
              placeholder="openid profile email w_member_social"
              value={formData.oauth_scopes || ''}
              onChange={(e) => handleChange('oauth_scopes', e.target.value)}
            />
          </div>
        );

      case 'youtube':
        return (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-[#f8fafc] border border-[#e2e8f0] text-xs text-[#64748b] space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#0f172a]">YouTube Data API v3</span>
                <a
                  href="https://console.cloud.google.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#8b5cf6] hover:underline flex items-center gap-1 font-bold text-[11px]"
                >
                  console.cloud.google.com <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p>Fetches trending YouTube Shorts &amp; high-velocity video tags.</p>
            </div>

            <div className="relative">
              <Input
                label="YouTube API Key"
                type={showSecret.api_key ? 'text' : 'password'}
                placeholder="AIzaSy..."
                value={formData.api_key || ''}
                onChange={(e) => handleChange('api_key', e.target.value)}
              />
              <button
                type="button"
                onClick={() => toggleSecret('api_key')}
                className="absolute right-3 top-9 text-[#94a3b8] hover:text-[#0f172a]"
              >
                {showSecret.api_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
        );

      default:
        return (
          <div className="space-y-4">
            <Input
              label="API Key"
              type="password"
              placeholder="Enter API key..."
              value={formData.api_key || ''}
              onChange={(e) => handleChange('api_key', e.target.value)}
            />
          </div>
        );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Configure ${source.name}`}
      description={`Set OAuth 2.0 Credentials & API Keys for ${source.platform.toUpperCase()}`}
      maxWidth="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-[#8b5cf6]" />
            <span>Encrypted in PostgreSQL</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="light" size="sm" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSave}
              isLoading={isSaving}
              leftIcon={<Save className="w-4 h-4 text-[#a78bfa]" />}
            >
              Save Credentials
            </Button>
          </div>
        </div>
      }
    >
      <form onSubmit={handleSave} className="space-y-4">
        {renderPlatformForm()}
      </form>
    </Modal>
  );
};
