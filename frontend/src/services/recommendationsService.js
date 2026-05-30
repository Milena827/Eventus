import apiClient from './api';

export const recommendationsService = {
    async getRecommendations(userId) {
        const response = await apiClient.get(`/recommendations/${userId}`);
        return response.data;
    },

    async addAction(userId, action) {
        const response = await apiClient.post(`/recommendations/${userId}/actions`, action);
        return response.data;
    },

    async getActions(userId) {
        const response = await apiClient.get(`/recommendations/${userId}/actions`);
        return response.data;
    },
};