import { trendsApi } from '../api/trends';
import { trendRunsApi } from '../api/trendRuns';
import { trendSourcesApi } from '../api/trendSources';

export const trendService = {
  // Trends
  getTrends: trendsApi.getTrends,
  getTrendDetail: trendsApi.getTrendDetail,
  batchReview: trendsApi.batchReview,

  // Runs
  getRuns: trendRunsApi.getRuns,
  getRunById: trendRunsApi.getRunById,
  createRun: trendRunsApi.createRun,
  cancelRun: trendRunsApi.cancelRun,

  // Sources
  getSources: trendSourcesApi.getSources,
  getSourceById: trendSourcesApi.getSourceById,
  updateSource: trendSourcesApi.updateSource,
  enableSource: trendSourcesApi.enableSource,
  disableSource: trendSourcesApi.disableSource,
};

