import apiClient from './api';

export const ragService = {
  async addDocument(title, content, source = null, metadata = null) {
    const response = await apiClient.post('/api/rag/documents', {
      title,
      content,
      source,
      metadata,
    });
    return response.data;
  },

  async listDocuments() {
    const response = await apiClient.get('/api/rag/documents');
    return response.data.documents;
  },

  async deleteDocument(docId) {
    const response = await apiClient.delete(`/api/rag/documents/${docId}`);
    return response.data;
  },

  async search(query, topK = 3) {
    const response = await apiClient.post('/api/rag/search', {
      query,
      top_k: topK,
    });
    return response.data.results;
  },

  async generate(query, model = 'llama2', topK = 3) {
    const response = await apiClient.post('/api/rag/generate', {
      query,
      model,
      top_k: topK,
    });
    return response.data;
  },

  async getStats() {
    const response = await apiClient.get('/api/rag/stats');
    return response.data;
  },
};

export default ragService;
