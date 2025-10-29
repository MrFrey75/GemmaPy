import apiClient from './api';

export const metricsService = {
  async getDashboard(days = 7) {
    const response = await apiClient.get('/api/metrics/dashboard', {
      params: { days },
    });
    return response.data;
  },

  async getTimeSeries(days = 7, interval = 'hour') {
    const response = await apiClient.get('/api/metrics/timeseries', {
      params: { days, interval },
    });
    return response.data.data;
  },

  async getEndpointStats(days = 7) {
    const response = await apiClient.get('/api/metrics/endpoints', {
      params: { days },
    });
    return response.data.endpoints;
  },

  async rateMetric(metricId, rating) {
    const response = await apiClient.post(`/api/metrics/${metricId}/rate`, {
      rating,
    });
    return response.data;
  },
};

export default metricsService;
