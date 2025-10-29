import apiClient from './api';

export const comparisonService = {
  async compareModels(prompt, models, system = null, temperature = 0.7) {
    const response = await apiClient.post('/api/compare/models', {
      prompt,
      models,
      system,
      temperature,
    });
    return response.data;
  },

  async listComparisons(limit = 50) {
    const response = await apiClient.get('/api/compare/comparisons', {
      params: { limit },
    });
    return response.data.comparisons;
  },

  async getComparison(comparisonId) {
    const response = await apiClient.get(`/api/compare/comparisons/${comparisonId}`);
    return response.data.comparison;
  },

  async deleteComparison(comparisonId) {
    const response = await apiClient.delete(`/api/compare/comparisons/${comparisonId}`);
    return response.data;
  },

  async rateResponse(responseId, rating) {
    const response = await apiClient.post(`/api/compare/responses/${responseId}/rate`, {
      rating,
    });
    return response.data;
  },

  async getModelRankings(days = 30) {
    const response = await apiClient.get('/api/compare/rankings', {
      params: { days },
    });
    return response.data.rankings;
  },

  async getStatistics() {
    const response = await apiClient.get('/api/compare/statistics');
    return response.data.statistics;
  },
};

export default comparisonService;
