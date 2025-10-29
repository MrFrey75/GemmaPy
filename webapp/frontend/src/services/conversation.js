import apiClient from './api';

export const conversationService = {
  async list(limit = 50) {
    const response = await apiClient.get('/api/conversations', {
      params: { limit },
    });
    return response.data.conversations;
  },

  async create(title, model = 'llama2', systemPrompt = null) {
    const response = await apiClient.post('/api/conversations', {
      title,
      model,
      system_prompt: systemPrompt,
    });
    return response.data;
  },

  async get(conversationId) {
    const response = await apiClient.get(`/api/conversations/${conversationId}`);
    return response.data.conversation;
  },

  async update(conversationId, title) {
    const response = await apiClient.put(`/api/conversations/${conversationId}`, {
      title,
    });
    return response.data;
  },

  async delete(conversationId) {
    const response = await apiClient.delete(`/api/conversations/${conversationId}`);
    return response.data;
  },

  async addMessage(conversationId, role, content) {
    const response = await apiClient.post(
      `/api/conversations/${conversationId}/messages`,
      { role, content }
    );
    return response.data;
  },

  async generate(conversationId, message, temperature = 0.7) {
    const response = await apiClient.post(
      `/api/conversations/${conversationId}/generate`,
      {
        message,
        temperature,
        use_cache: true,
        use_retry: true,
      }
    );
    return response.data;
  },

  async search(query, limit = 20) {
    const response = await apiClient.get('/api/conversations/search', {
      params: { q: query, limit },
    });
    return response.data.results;
  },

  async getStatistics() {
    const response = await apiClient.get('/api/conversations/statistics');
    return response.data.statistics;
  },
};

export default conversationService;
