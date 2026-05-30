<template>
  <div class="auth-card">
    <h2>Вход</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label class="form-label">Email</label>
        <input v-model="email" type="email" class="form-control" required placeholder="student@utmn.ru">
      </div>
      <div class="form-group">
        <label class="form-label">Пароль</label>
        <input v-model="password" type="password" class="form-control" required>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:10px;" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
    </form>
    <p class="text-center mt-4">
      Нет аккаунта? <router-link to="/register" style="color:#009fe3;">Регистрация</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/authService';

const router = useRouter();
const authStore = useAuthStore();
const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

async function handleLogin() {
  loading.value = true; error.value = '';
  try {
    const data = await authService.login(email.value, password.value);
    authStore.setAuth(data);
    router.push('/feed');
  } catch (err) {
    error.value = err.response?.data?.detail || 'Неверный email или пароль';
  } finally { loading.value = false; }
}
</script>