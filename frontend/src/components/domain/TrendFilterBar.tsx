import React from 'react';
import { Search, RotateCcw } from 'lucide-react';
import { Input, Select } from '../common/Input';
import type { TrendQueryParams } from '../../types/trend';

interface TrendFilterBarProps {
  filters: TrendQueryParams;
  onChange: (newFilters: TrendQueryParams) => void;
  totalCount?: number;
}

export const TrendFilterBar: React.FC<TrendFilterBarProps> = ({
  filters,
  onChange,
  totalCount,
}) => {
  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'pending_review', label: '⏳ Pending Review' },
    { value: 'approved', label: '✅ Approved' },
    { value: 'prompt_generated', label: '✨ Prompt Ready' },
    { value: 'scored', label: '📊 Scored' },
    { value: 'discovered', label: '🔍 Discovered' },
    { value: 'rejected', label: '❌ Rejected' },
  ];

  const categoryOptions = [
    { value: '', label: 'All Categories' },
    { value: 'ai_visual', label: 'AI Visual & Art' },
    { value: 'product_marketing', label: 'Product Marketing' },
    { value: 'lifestyle', label: 'Lifestyle & Viral' },
    { value: 'entertainment', label: 'Entertainment' },
    { value: 'technology', label: 'Technology' },
    { value: 'fashion', label: 'Fashion & Beauty' },
  ];

  const scoreOptions = [
    { value: '', label: 'All Scores' },
    { value: '80', label: 'High Impact (≥ 80)' },
    { value: '70', label: 'Threshold (≥ 70)' },
    { value: '50', label: 'Medium (≥ 50)' },
  ];

  const hasActiveFilters = Boolean(
    filters.search || filters.status || filters.category || filters.minimum_score
  );

  const handleReset = () => {
    onChange({ page: 1, page_size: filters.page_size || 12 });
  };

  return (
    <div className="bg-[#ffffff] border border-slate-200 rounded-2xl p-4 shadow-xs mb-6">
      <div className="flex flex-col md:flex-row items-center gap-3 justify-between">
        {/* Search input */}
        <div className="w-full md:w-80">
          <Input
            placeholder="Search trend title or keywords..."
            value={filters.search || ''}
            onChange={(e) => onChange({ ...filters, search: e.target.value, page: 1 })}
            leftIcon={<Search className="w-4 h-4 text-slate-400" />}
          />
        </div>

        {/* Dropdowns & Reset Filter */}
        <div className="flex items-center gap-2.5 w-full md:w-auto flex-wrap sm:flex-nowrap">
          <Select
            options={statusOptions}
            value={filters.status || ''}
            onChange={(e) => onChange({ ...filters, status: e.target.value, page: 1 })}
            className="w-full sm:w-44"
          />

          <Select
            options={categoryOptions}
            value={filters.category || ''}
            onChange={(e) => onChange({ ...filters, category: e.target.value, page: 1 })}
            className="w-full sm:w-44"
          />

          <Select
            options={scoreOptions}
            value={filters.minimum_score !== undefined ? String(filters.minimum_score) : ''}
            onChange={(e) =>
              onChange({
                ...filters,
                minimum_score: e.target.value ? Number(e.target.value) : undefined,
                page: 1,
              })
            }
            className="w-full sm:w-36"
          />

          {hasActiveFilters && (
            <button
              onClick={handleReset}
              className="p-2.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-xl border border-slate-200 transition-colors cursor-pointer shrink-0"
              title="Reset Filters"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {totalCount !== undefined && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing results for: <strong className="text-slate-900">{totalCount} trends</strong>
          </span>
          {hasActiveFilters && (
            <span className="text-[#8b5cf6] font-semibold text-[11px]">Filters active</span>
          )}
        </div>
      )}
    </div>
  );
};
