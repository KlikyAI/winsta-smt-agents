import React from 'react';
import { ArrowRight, Calendar, CheckCircle, Check } from 'lucide-react';
import type { TrendListItem } from '../../types/trend';
import { Card } from '../common/Card';
import { TrendStatusBadge } from '../common/Badge';
import { ScoreMeter } from '../common/ScoreMeter';
import { Button } from '../common/Button';

interface TrendCardProps {
  trend: TrendListItem;
  onViewDetail: (trend: TrendListItem) => void;
  onReview?: (trend: TrendListItem) => void;
  isSelected?: boolean;
  onToggleSelect?: (trendId: string) => void;
}

export const TrendCard: React.FC<TrendCardProps> = ({
  trend,
  onViewDetail,
  onReview,
  isSelected = false,
  onToggleSelect,
}) => {
  return (
    <Card
      hoverable
      className={`flex flex-col justify-between h-full group bg-white border transition-all p-5 rounded-2xl relative ${
        isSelected ? 'border-[#8b5cf6] ring-2 ring-[#8b5cf6]/30 shadow-md' : 'border-slate-200'
      }`}
      onClick={() => onViewDetail(trend)}
    >
      <div>
        {/* Top bar: Select Checkbox + Category + Status */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2 min-w-0">
            {onToggleSelect && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleSelect(trend.id);
                }}
                className={`w-4 h-4 rounded border flex items-center justify-center transition-all cursor-pointer shrink-0 ${
                  isSelected
                    ? 'bg-[#8b5cf6] border-[#8b5cf6] text-white shadow-xs'
                    : 'border-slate-300 hover:border-[#8b5cf6] bg-white'
                }`}
                title={isSelected ? 'Deselect trend' : 'Select for batch action'}
              >
                {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
              </button>
            )}
            <span className="clova-eyebrow text-slate-500 text-[10px] truncate max-w-[120px] block">
              {trend.category ? trend.category.replace(/_/g, ' ') : 'General'}
            </span>
          </div>

          <div className="shrink-0">
            <TrendStatusBadge status={trend.status} />
          </div>
        </div>

        {/* Title */}
        <h4
          className="text-sm font-bold font-sans text-slate-900 group-hover:text-[#8b5cf6] transition-colors line-clamp-2 leading-snug min-h-[2.6rem] break-words"
          title={trend.title}
        >
          {trend.title}
        </h4>

        {/* Date info */}
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-2.5">
          <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="truncate">Discovered {new Date(trend.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      {/* Footer: Score + Review Action */}
      <div className="mt-5 pt-3.5 border-t border-slate-100 flex items-center justify-between gap-2">
        <div className="shrink-0">
          <ScoreMeter score={trend.overall_score} size="md" />
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {trend.status === 'pending_review' && onReview && (
            <Button
              variant="lime"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onReview(trend);
              }}
              leftIcon={<CheckCircle className="w-3.5 h-3.5" />}
            >
              Review
            </Button>
          )}

          <Button
            variant="light"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onViewDetail(trend);
            }}
            rightIcon={<ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />}
          >
            Details
          </Button>
        </div>
      </div>
    </Card>
  );
};
