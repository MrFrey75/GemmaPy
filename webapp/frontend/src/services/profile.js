import apiClient from './api';

export const profileService = {
  async getProfile() {
    const response = await apiClient.get('/api/profile');
    return response.data.profile;
  },

  async updateProfile(profileData) {
    const response = await apiClient.put('/api/profile', profileData);
    return response.data.profile;
  },

  async changePassword(currentPassword, newPassword) {
    const response = await apiClient.put('/api/profile/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  async deleteAccount(password) {
    const response = await apiClient.delete('/api/profile', {
      data: { password },
    });
    return response.data;
  },
};

export default profileService;
