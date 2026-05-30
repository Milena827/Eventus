import apiClient from './api';

export const eventsService = {
    async getEvents(params = {}) {
        const response = await apiClient.get('/events/', { params });
        return response.data;
    },

    async getEvent(id) {
        const response = await apiClient.get(`/events/${id}`);
        return response.data;
    },

    async createEvent(data) {
        const response = await apiClient.post('/events/', data);
        return response.data;
    },
};