import apiClient from './api';
import { log } from '../utils/logger';

export const authService = {
    async register(data) {
        log.auth.info('Регистрация пользователя', { email: data.email });
        const response = await apiClient.post('/auth/register', data);
        return response.data;
    },

    async login(email, password) {
        log.auth.info('Вход в систему', { email });
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        const response = await apiClient.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    async getMe() {
        const response = await apiClient.get('/auth/me');
        return response.data;
    },
};