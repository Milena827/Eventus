import apiClient from './api';

export const userService = {
    async getUser(id) {
        const response = await apiClient.get(`/users/${id}`);
        return response.data;
    },

    async getFullProfile(id) {
        const response = await apiClient.get(`/users/${id}/full-profile`);
        return response.data;
    },

    async addTestResults(userId, results) {
        const response = await apiClient.post(`/users/${userId}/test-results`, results);
        return response.data;
    },

    async addInterests(userId, interests) {
        const response = await apiClient.post(`/users/${userId}/interests`, interests);
        return response.data;
    },

    async deleteInterest(userId, categoryId) {
        const response = await apiClient.delete(`/users/${userId}/interests/${categoryId}`);
        return response.data;
    },
};