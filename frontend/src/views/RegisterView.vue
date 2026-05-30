<template>
  <div class="auth-card">
    <h2>Регистрация</h2>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>
    <form @submit.prevent="handleRegister">
      <div class="form-group">
        <label class="form-label">ФИО</label>
        <input v-model="form.full_name" type="text" class="form-control" required placeholder="Иванов Иван">
      </div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input v-model="form.email" type="email" class="form-control" required placeholder="student@utmn.ru">
      </div>
      <div class="form-group">
        <label class="form-label">Пароль</label>
        <input v-model="form.password" type="password" class="form-control" required>
      </div>
      <div class="row">
        <div class="col-6 form-group">
          <label class="form-label">Факультет</label>
          <input v-model="form.faculty" type="text" class="form-control" required placeholder="ИМиКН">
        </div>
        <div class="col-6 form-group">
          <label class="form-label">Курс (1-6)</label>
          <input v-model="form.course" type="number" min="1" max="6" class="form-control" required>
        </div>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:10px;" :disabled="loading">
        {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
      </button>
    </form>
    <p class="text-center mt-4">
      Уже есть аккаунт? <router-link to="/login" style="color:#009fe3;">Войти</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/authService';

const router = useRouter();
const authStore = useAuthStore();
const form = reactive({
  email: '',
  password: '',
  full_name: '',
  course: 1,
  faculty: '',
});
const loading = ref(false);
const error = ref('');
const success = ref('');

async function handleRegister() {
  loading.value = true;
  error.value = '';
  success.value = '';
  try {
    const data = await authService.register(form);
    authStore.setAuth(data);
    success.value = '✅ Регистрация успешна! Сейчас вы перейдёте в профиль для заполнения баллов и интересов...';
    setTimeout(() => router.push('/profile'), 2000);
  } catch (err) {
    error.value = err.response?.data?.detail || 'Ошибка регистрации';
  } finally {
    loading.value = false;
  }
}
</script>