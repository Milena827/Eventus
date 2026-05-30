import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import HomeView from '../views/HomeView.vue';

const routes = [
    { path: '/', name: 'home', component: HomeView },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue') },
    { path: '/feed', name: 'feed', component: () => import('../views/FeedView.vue'), meta: { requiresAuth: true } },
    { path: '/events', name: 'events', component: () => import('../views/EventsView.vue') },
    { path: '/events/:id', name: 'event-detail', component: () => import('../views/EventDetailView.vue') },
    { path: '/profile', name: 'profile', component: () => import('../views/ProfileView.vue'), meta: { requiresAuth: true } },
    { path: '/favorites', name: 'favorites', component: () => import('../views/FavoritesView.vue'), meta: { requiresAuth: true } },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to, from) => {
    const authStore = useAuthStore();
    if (to.meta.requiresAuth && !authStore.isLoggedIn) {
        return '/login';
    }
});

export default router;