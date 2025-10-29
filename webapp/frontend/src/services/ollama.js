import apiClient from './api';

export const ollamaService = {
  async getStatus() {
    const response = await apiClient.get('/api/ollama/status');
    return response.data;
  },

  async listModels() {
    const response = await apiClient.get('/api/ollama/models');
    return response.data.models;
  },

  async getModelInfo(modelName) {
    const response = await apiClient.get(`/api/ollama/models/${modelName}`);
    return response.data;
  },

  async pullModel(modelName) {
    const response = await apiClient.post('/api/ollama/models/pull', {
      model: modelName,
    });
    return response.data;
  },

  async deleteModel(modelName) {
    const response = await apiClient.delete(`/api/ollama/models/${modelName}`);
    return response.data;
  },

  async generate(model, prompt, system = null, temperature = 0.7, maxTokens = null) {
    const response = await apiClient.post('/api/ollama/generate', {
      model,
      prompt,
      system,
      temperature,
      max_tokens: maxTokens,
      use_cache: true,
      use_retry: true,
    });
    return response.data;
  },

  async *generateStream(model, prompt, system = null, temperature = 0.7) {
    const response = await apiClient.post(
      '/api/ollama/generate/stream',
      {
        model,
        prompt,
        system,
        temperature,
      },
      {
        responseType: 'stream',
      }
    );

    const reader = response.data.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const json = JSON.parse(line.slice(6));
              if (json.chunk) {
                yield json.chunk;
              }
            } catch (e) {
              // Ignore parsing errors
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  async chat(model, messages, temperature = 0.7) {
    const response = await apiClient.post('/api/ollama/chat', {
      model,
      messages,
      temperature,
    });
    return response.data;
  },

  async embeddings(model, text) {
    const response = await apiClient.post('/api/ollama/embeddings', {
      model,
      text,
    });
    return response.data;
  },
};

export default ollamaService;
