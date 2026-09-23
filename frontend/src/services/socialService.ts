import { socialMediaApi } from '../api/socialMedia';

export const socialService = {
  ...socialMediaApi,

  // Enhanced helper methods
  fetchBriefsData: async (page = 1, pageSize = 20) => {
    const res = await socialMediaApi.getBriefs(page, pageSize);
    return res.data;
  },

  fetchConnectionsData: async () => {
    const res = await socialMediaApi.getConnections();
    return res.data;
  },

  fetchCampaignsData: async (status?: string, page = 1, pageSize = 20) => {
    const res = await socialMediaApi.getCampaigns(status, page, pageSize);
    return res.data;
  },
};

