import React, { useState, useEffect } from 'react';
import {
  Flame,
  RefreshCw,
  Plus,
  ChevronLeft,
  ChevronRight,
  Compass,
  Play,
  CheckCircle2,
  XCircle,
  Download,
  FileSpreadsheet,
  FileCode,
  CheckSquare,
  Square,
  X,
} from 'lucide-react';
import { TrendFilterBar } from '../../components/domain/TrendFilterBar';
import { TrendCard } from '../../components/domain/TrendCard';
import { TrendDetailModal } from '../../components/domain/TrendDetailModal';
import { ReviewActionModal } from '../../components/domain/ReviewActionModal';
import { Button } from '../../components/common/Button';
import { Spinner } from '../../components/common/Tabs';
import type { TrendListItem, TrendQueryParams } from '../../types/trend';
import { trendsApi } from '../../api/trends';
import { useToast } from '../../context/ToastContext';

interface TrendsPageProps {
  onTriggerRun: () => void;
}

export const TrendsPage: React.FC<TrendsPageProps> = ({ onTriggerRun }) => {
  const { addToast } = useToast();
  const [trends, setTrends] = useState<TrendListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<TrendQueryParams>({ page: 1, page_size: 12 });
  const [selectedTrend, setSelectedTrend] = useState<TrendListItem | null>(null);
  const [reviewTrend, setReviewTrend] = useState<TrendListItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Batch Selection State
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  const fetchTrends = async () => {
    setIsLoading(true);
    try {
      const res = await trendsApi.getTrends(filters);
      setTrends(res.data?.items || []);
      setTotal(res.data?.total || 0);
      setTotalPages(res.data?.total_pages || 1);
    } catch (err: any) {
      addToast('error', 'Failed to load trends', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, [filters]);

  // Batch toggle handlers
  const handleToggleSelect = (trendId: string) => {
    const next = new Set(selectedIds);
    if (next.has(trendId)) {
      next.delete(trendId);
    } else {
      next.add(trendId);
    }
    setSelectedIds(next);
  };

  const handleSelectAllOnPage = () => {
    if (selectedIds.size === trends.length && trends.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(trends.map((t) => t.id)));
    }
  };

  // Batch Review Action
  const handleBatchReview = async (decision: 'approve' | 'reject') => {
    if (selectedIds.size === 0) return;
    setIsBatchProcessing(true);
    try {
      const res = await trendsApi.batchReview({
        trend_ids: Array.from(selectedIds),
        decision,
        notes: `Batch ${decision} from Trends Explorer`,
      });
      addToast(
        decision === 'approve' ? 'success' : 'info',
        `Batch ${decision === 'approve' ? 'Approved' : 'Rejected'}`,
        `Successfully updated ${res.data.processed_count} trends`
      );
      setSelectedIds(new Set());
      fetchTrends();
    } catch (err: any) {
      addToast('error', 'Batch Review Failed', err.message || 'Error processing batch action');
    } finally {
      setIsBatchProcessing(false);
    }
  };

  // Export Engine (Point 6)
  const exportToCSV = (itemsToExport: TrendListItem[], filenamePrefix = 'winsta-trends') => {
    if (itemsToExport.length === 0) return;
    const headers = ['ID', 'Title', 'Category', 'Overall Score', 'Status', 'Discovered Date'];
    const rows = itemsToExport.map((t) => [
      `"${t.id}"`,
      `"${(t.title || '').replace(/"/g, '""')}"`,
      `"${t.category || 'General'}"`,
      t.overall_score || 0,
      `"${t.status}"`,
      `"${new Date(t.created_at).toISOString()}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filenamePrefix}-${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    addToast('success', 'Export Completed', `Exported ${itemsToExport.length} trends to CSV.`);
  };

  const exportToJSON = (itemsToExport: TrendListItem[], filenamePrefix = 'winsta-trends') => {
    if (itemsToExport.length === 0) return;
    const jsonContent = JSON.stringify(itemsToExport, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filenamePrefix}-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    addToast('success', 'Export Completed', `Exported ${itemsToExport.length} trends to JSON.`);
  };

  const getSelectedTrends = (): TrendListItem[] => {
    return trends.filter((t) => selectedIds.has(t.id));
  };

  return (
    <div className="space-y-6 pb-20">
      {/* Header with Title & Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-[#0f172a] text-[#8b5cf6] flex items-center justify-center">
              <Flame className="w-4 h-4 fill-current" />
            </span>
            <h2 className="text-2xl font-bold text-[#0f172a] tracking-tight">
              Trends Explorer
            </h2>
          </div>
          <p className="text-xs text-[#64748b] mt-1 font-medium">
            Explore curated AI trends, inspect image/video prompts, and submit human review decisions for Sarah Agent handoff.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Export Dropdown Menu */}
          <div className="relative">
            <Button
              variant="light"
              size="sm"
              onClick={() => setIsExportOpen(!isExportOpen)}
              leftIcon={<Download className="w-3.5 h-3.5 text-[#8b5cf6]" />}
            >
              Export
            </Button>

            {isExportOpen && (
              <div className="absolute right-0 mt-2 w-48 rounded-2xl bg-white border border-slate-200 shadow-xl py-1.5 z-50 animate-fade-in">
                <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 mb-1">
                  Export Options
                </div>
                <button
                  onClick={() => {
                    exportToCSV(trends, 'winsta-page-trends');
                    setIsExportOpen(false);
                  }}
                  className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-slate-50 flex items-center gap-2 cursor-pointer"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Export Page to CSV</span>
                </button>
                <button
                  onClick={() => {
                    exportToJSON(trends, 'winsta-page-trends');
                    setIsExportOpen(false);
                  }}
                  className="w-full px-3 py-2 text-left text-xs font-semibold text-slate-700 hover:bg-slate-50 flex items-center gap-2 cursor-pointer"
                >
                  <FileCode className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Export Page to JSON</span>
                </button>
              </div>
            )}
          </div>

          <Button variant="light" size="sm" onClick={fetchTrends} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
            Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={onTriggerRun} leftIcon={<Plus className="w-4 h-4 text-[#8b5cf6]" />}>
            New Discovery Run
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <TrendFilterBar filters={filters} onChange={setFilters} totalCount={total} />

      {/* Select All Toggle Bar */}
      {trends.length > 0 && !isLoading && (
        <div className="flex items-center justify-between px-1">
          <button
            onClick={handleSelectAllOnPage}
            className="flex items-center gap-2 text-xs font-bold text-slate-700 hover:text-slate-900 cursor-pointer"
          >
            {selectedIds.size === trends.length && trends.length > 0 ? (
              <CheckSquare className="w-4 h-4 text-[#8b5cf6]" />
            ) : (
              <Square className="w-4 h-4 text-slate-400" />
            )}
            <span>
              {selectedIds.size === trends.length ? 'Deselect All on Page' : 'Select All on Page'}
            </span>
          </button>

          {selectedIds.size > 0 && (
            <span className="text-xs font-semibold text-[#8b5cf6]">
              {selectedIds.size} of {trends.length} selected
            </span>
          )}
        </div>
      )}

      {/* Trends Grid or Empty State */}
      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center gap-3">
          <Spinner size="md" />
          <p className="text-xs font-semibold text-[#64748b]">Loading trends from database...</p>
        </div>
      ) : trends.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {trends.map((trend) => (
              <TrendCard
                key={trend.id}
                trend={trend}
                onViewDetail={setSelectedTrend}
                onReview={setReviewTrend}
                isSelected={selectedIds.has(trend.id)}
                onToggleSelect={handleToggleSelect}
              />
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-6">
              <Button
                variant="light"
                size="sm"
                disabled={(filters.page || 1) <= 1}
                onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                leftIcon={<ChevronLeft className="w-4 h-4" />}
              >
                Previous
              </Button>
              <span className="text-xs font-bold text-[#0f172a]">
                Page {filters.page || 1} of {totalPages}
              </span>
              <Button
                variant="light"
                size="sm"
                disabled={(filters.page || 1) >= totalPages}
                onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                rightIcon={<ChevronRight className="w-4 h-4" />}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        /* Empty State */
        <div className="bg-[#ffffff] rounded-2xl border border-[#e2e8f0] p-8 sm:p-12 text-center max-w-xl mx-auto shadow-xs">
          <div className="w-14 h-14 rounded-full bg-[#f8fafc] border border-[#e2e8f0] text-[#0f172a] flex items-center justify-center mx-auto mb-4">
            <Compass className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-[#0f172a]">No Trends Found</h3>
          <p className="text-xs text-[#64748b] mt-1.5 leading-relaxed max-w-md mx-auto">
            The database does not have any trends matching your query. Trigger a <strong>Discovery Run</strong> to collect viral concepts from Instagram, TikTok, YouTube, X, and Google Trends.
          </p>

          <div className="mt-6 flex items-center justify-center gap-3">
            <Button
              variant="primary"
              onClick={onTriggerRun}
              leftIcon={<Play className="w-3.5 h-3.5 fill-[#8b5cf6] text-[#8b5cf6]" />}
            >
              Start Discovery Run Now
            </Button>
          </div>
        </div>
      )}

      {/* FLOATING BATCH ACTION BAR (Point 2 & Point 6) */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-[#0f172a] text-white px-6 py-3.5 rounded-full shadow-2xl border border-slate-700 flex items-center gap-4 animate-modal-scale max-w-[90vw] flex-wrap justify-between">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-[#8b5cf6] text-white flex items-center justify-center font-bold text-xs">
              {selectedIds.size}
            </span>
            <span className="text-xs font-bold whitespace-nowrap">Trends Selected</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Batch Approve */}
            <button
              onClick={() => handleBatchReview('approve')}
              disabled={isBatchProcessing}
              className="px-3.5 py-1.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Batch Approve & Dispatch</span>
            </button>

            {/* Batch Reject */}
            <button
              onClick={() => handleBatchReview('reject')}
              disabled={isBatchProcessing}
              className="px-3.5 py-1.5 rounded-full bg-rose-600/80 hover:bg-rose-600 text-white text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer disabled:opacity-50"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Batch Reject</span>
            </button>

            {/* Batch Export CSV */}
            <button
              onClick={() => exportToCSV(getSelectedTrends(), 'winsta-selected-trends')}
              className="px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer border border-slate-700"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Export CSV</span>
            </button>

            {/* Deselect All */}
            <button
              onClick={() => setSelectedIds(new Set())}
              className="p-1.5 rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
              title="Deselect All"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <TrendDetailModal
        trendItem={selectedTrend}
        isOpen={!!selectedTrend}
        onClose={() => setSelectedTrend(null)}
        onReview={setReviewTrend}
      />

      <ReviewActionModal
        trend={reviewTrend}
        isOpen={!!reviewTrend}
        onClose={() => setReviewTrend(null)}
        onSuccess={fetchTrends}
      />
    </div>
  );
};
