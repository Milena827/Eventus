import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { log } from '../utils/logger';

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '');
    const user = ref(JSON.parse(localStorage.getItem('user') || 'null'));

    const isLoggedIn = computed(() => !!token.value);
    const userName = computed(() => user.value?.full_name || 'Пользователь');
    const userId = computed(() => user.value?.id || null);

    function setAuth(data) {
        token.value = data.access_token;
        user.value = {
            id: data.user_id,
            email: data.email,
            full_name: data.full_name,
        };
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(user.value));
        log.auth.info('Авторизация успешна', { email: data.email });
    }

    function logout() {
        token.value = '';
        user.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        log.auth.info('Выход из системы');
    }

    return { token, user, isLoggedIn, userName, userId, setAuth, logout };
});