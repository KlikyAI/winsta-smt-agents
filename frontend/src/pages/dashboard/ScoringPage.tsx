import React, { useState, useEffect } from 'react';
import { Sliders, Save, RotateCcw, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import type { ScoringWeightItem } from '../../types/scoring';
import { scoringApi } from '../../api/scoring';
import { useToast } from '../../context/ToastContext';

export const ScoringPage: React.FC = () => {
  const { addToast } = useToast();
  const [weights, setWeights] = useState<ScoringWeightItem[]>([]);
  const [version, setVersion] = useState(1);
  const [isSaving, setIsSaving] = useState(false);

  const fetchSettings = async () => {
    try {
      const res = await scoringApi.getSettings();
      setWeights(res.data.weights || []);
      setVersion(res.data.version || 1);
    } catch (err: any) {
      addToast('error', 'Failed to fetch scoring settings', err.message);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const totalWeight = weights.reduce((acc, curr) => acc + Number(curr.weight || 0), 0);
  const isValidTotal = Math.abs(totalWeight - 100.0) < 0.01;

  const handleWeightChange = (index: number, newWeight: number) => {
    const updated = [...weights];
    updated[index] = { ...updated[index], weight: newWeight };
    setWeights(updated);
  };

  const handleSave = async () => {
    if (!isValidTotal) {
      addToast('error', 'Invalid Weight Sum', `Total weights must sum to exactly 100%. Current sum: ${totalWeight.toFixed(1)}%`);
      return;
    }

    setIsSaving(true);
    try {
      const res = await scoringApi.updateSettings({ weights });
      setVersion(res.data.version);
      addToast('success', 'Scoring Configuration Saved', `Updated to Version v${res.data.version}. Weights successfully recalculated.`);
    } catch (err: any) {
      addToast('error', 'Update Failed', err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const signalDescriptions: Record<string, string> = {
    freshness: 'Measures how recently the trend emerged across social feeds.',
    velocity: 'Measures acceleration rate of views, likes, and shares.',
    engagement_quality: 'Ratio of comments & shares relative to total impressions.',
    winsta_relevance: 'Alignment with Winsta AI marketing and audience domain.',
    visual_generatability: 'Feasibility of producing stunning AI image/video outputs.',
    novelty: 'Degree of uniqueness compared to previously generated concepts.',
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-[#0f172a] text-[#8b5cf6] flex items-center justify-center">
              <Sliders className="w-4 h-4" />
            </span>
            <h2 className="text-2xl font-bold text-[#0f172a] tracking-tight">
              Scoring Studio
            </h2>
          </div>
          <p className="text-xs text-[#64748b] mt-1 font-medium">
            Configure multi-signal weights for deterministic trend scoring. Total weight must equal 100%.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="lime">Active: v{version}</Badge>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            isLoading={isSaving}
            disabled={!isValidTotal}
            leftIcon={<Save className="w-3.5 h-3.5 text-[#8b5cf6]" />}
          >
            Save Changes
          </Button>
        </div>
      </div>

      {/* Total Weight Counter Banner */}
      <div
        className={`p-5 rounded-2xl border shadow-xs flex items-center justify-between transition-colors ${
          isValidTotal
            ? 'bg-[#ffffff] border-[#e2e8f0] text-[#0f172a]'
            : 'bg-[#8b5cf6] border-[#0f172a] text-[#ffffff]'
        }`}
      >
        <div className="flex items-center gap-3">
          {isValidTotal ? (
            <CheckCircle2 className="w-5 h-5 text-[#0f172a]" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-[#ffffff]" />
          )}
          <div>
            <span className="text-sm font-bold block">
              Total Weight: {totalWeight.toFixed(1)}% / 100.0%
            </span>
            <span className="text-xs opacity-80 font-medium">
              {isValidTotal
                ? 'Weights are balanced and ready to be applied.'
                : `Adjust signal weights so the sum reaches exactly 100.0% (${(100 - totalWeight).toFixed(1)}% remaining).`}
            </span>
          </div>
        </div>

        <Button variant="light" size="sm" onClick={fetchSettings} leftIcon={<RotateCcw className="w-3.5 h-3.5" />}>
          Reset
        </Button>
      </div>

      {/* Sliders Grid */}
      <Card className="space-y-6 p-6 bg-[#ffffff]">
        {weights.map((item, index) => (
          <div key={item.signal_type} className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-bold text-[#0f172a] capitalize block">
                  {item.signal_type.replace('_', ' ')}
                </span>
                <span className="text-xs text-[#64748b] font-medium">
                  {signalDescriptions[item.signal_type] || item.description || ''}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={1}
                  value={item.weight}
                  onChange={(e) => handleWeightChange(index, Number(e.target.value))}
                  className="w-16 bg-[#f8fafc] border border-[#e2e8f0] rounded-lg p-1.5 text-center text-sm font-bold font-mono text-[#0f172a] outline-none focus:border-[#0f172a]"
                />
                <span className="text-xs font-bold text-[#0f172a]">%</span>
              </div>
            </div>

            {/* Range Slider */}
            <input
              type="range"
              min={0}
              max={100}
              step={1}
              value={item.weight}
              onChange={(e) => handleWeightChange(index, Number(e.target.value))}
              className="w-full h-2 bg-[#f8fafc] border border-[#e2e8f0] rounded-lg appearance-none cursor-pointer accent-[#0f172a]"
            />
          </div>
        ))}
      </Card>
    </div>
  );
};
