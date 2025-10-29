import apiClient from './api';

export const costService = {
  async getSummary(period = 'month') {
    const response = await apiClient.get('/api/costs/summary', {
      params: { period },
    });
    return response.data;
  },

  async getProjection(period = 'month') {
    const response = await apiClient.get('/api/costs/projection', {
      params: { period },
    });
    return response.data;
  },
};

export const adminService = {
  async getAllCosts(period = 'month') {
    const response = await apiClient.get('/api/admin/costs/all', {
      params: { period },
    });
    return response.data;
  },

  async getPricing() {
    const response = await apiClient.get('/api/admin/costs/pricing');
    return response.data;
  },

  async updatePricing(model, inputCost, outputCost) {
    const response = await apiClient.put('/api/admin/costs/pricing', {
      model,
      input_cost: inputCost,
      output_cost: outputCost,
    });
    return response.data;
  },

  async listUsers() {
    const response = await apiClient.get('/api/admin/users');
    return response.data.users;
  },

  async createUser(username, password, isAdmin = false) {
    const response = await apiClient.post('/api/admin/users', {
      username,
      password,
      is_admin: isAdmin,
    });
    return response.data;
  },
};

export default { costService, adminService };
