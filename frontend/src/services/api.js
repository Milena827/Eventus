import axios from 'axios';
import { useAuthStore } from '../stores/authStore';
import { log } from '../utils/logger';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore();
        if (authStore.token) {
            config.headers.Authorization = `Bearer ${authStore.token}`;
        }
        return config;
    },
    (error) => {
        log.api.error('Ошибка запроса', error);
        return Promise.reject(error);
    }
);

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            const authStore = useAuthStore();
            authStore.logout();
            window.location.href = '/login';
        }
        log.api.error(`Ошибка ${error.response?.status || 'сети'}`, error.response?.data || error.message);
        return Promise.reject(error);
    }
);

export default apiClient;