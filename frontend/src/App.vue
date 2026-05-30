<template>
  <div id="app">
    <header class="header">
      <div class="header-inner">
        <router-link to="/" class="logo">
          <img class="logo-img" src="./assets/img/logo.png" alt="ИВЕНТУС" />
          <span>ИВЕНТУС</span>
        </router-link>

        <div class="header-actions">
          <template v-if="authStore.isLoggedIn">
            <router-link to="/feed" class="nav-link-header">Лента</router-link>
            <router-link to="/events" class="nav-link-header">Каталог</router-link>
            <router-link to="/favorites" class="nav-link-header">Избранное</router-link>
            <router-link to="/profile" class="user-icon" title="Профиль">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="7" r="4" stroke="white" stroke-width="2"/>
                <path d="M4 21V19C4 15.6863 6.68629 13 10 13H14C17.3137 13 20 15.6863 20 19V21" stroke="white" stroke-width="2"/>
              </svg>
            </router-link>
            <button class="logout-btn" @click="handleLogout">Выйти</button>
          </template>
          <template v-else>
            <button class="login-btn" @click="$router.push('/login')">Войти / Регистрация</button>
          </template>
        </div>
      </div>
    </header>

    <router-view />

    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-logo">
          <img class="logo-img" src="./assets/img/logo.png" alt="ИВЕНТУС" />
          <span>ИВЕНТУС</span>
        </div>
        <p><a href="https://github.com/Eventus0000/backend">GitHub</a></p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/authStore';

const router = useRouter();
const authStore = useAuthStore();

function handleLogout() {
  authStore.logout();
  router.push('/');
}
</script>