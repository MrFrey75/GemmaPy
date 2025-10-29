import apiClient from './api';

export const authService = {
  async login(username, password) {
    const response = await apiClient.post('/api/login', {
      username,
      password,
    });
    const { token, user } = response.data;
    
    // Store token and user info
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    
    return { token, user };
  },

  async logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getToken() {
    return localStorage.getItem('token');
  },

  getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  isAdmin() {
    const user = this.getUser();
    return user?.is_admin || false;
  },
};

export default authService;
