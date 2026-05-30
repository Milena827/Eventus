<template>
  <div class="main">
    <h1>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:8px;">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
      Избранное
    </h1>

    <p class="section-subtitle" v-if="favoriteEvents.length">
      Мероприятия, которые вы добавили в избранное
    </p>

    <div v-if="loading" class="text-center py-5">Загрузка...</div>

    <section v-else-if="favoriteEvents.length" class="cards">
      <div class="event-card" v-for="event in favoriteEvents" :key="event.id">
        <div class="card-image" @click="$router.push(`/events/${event.id}`)">
          <img
            v-if="event.image_url && event.image_url.startsWith('http')"
            :src="event.image_url"
            :alt="event.title"
          />
          <div v-else class="no-card-image">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </div>
        </div>
        <div class="card-body">
          <h3 @click="$router.push(`/events/${event.id}`)">{{ event.title }}</h3>
          <div class="card-meta" v-if="event.event_date">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {{ formatDate(event.event_date) }}
          </div>
          <button class="remove-btn" @click="removeFavorite(event.id)" title="Удалить из избранного">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            Удалить
          </button>
        </div>
      </div>
    </section>

    <div v-else class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
      <p>Вы пока не добавили ни одного мероприятия в избранное</p>
      <router-link to="/events" class="catalog-link">Перейти в каталог</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '../stores/authStore';
import { eventsService } from '../services/eventsService';
import { formatDate } from '../utils/dateFormatter';

const authStore = useAuthStore();
const favoriteEvents = ref([]);
const loading = ref(true);

async function loadFavorites() {
  const userId = authStore.userId;

  if (!userId) {
    loading.value = false;
    return;
  }

  const stored = localStorage.getItem(`fav_${userId}`);
  const favoriteIds = stored ? JSON.parse(stored) : [];

  if (!favoriteIds.length) {
    favoriteEvents.value = [];
    loading.value = false;
    return;
  }

  try {
    const allEvents = await eventsService.getEvents({ limit: 500 });
    const now = new Date();
    now.setHours(0, 0, 0, 0);

    favoriteEvents.value = allEvents.filter(event => {
      const isFavorite = favoriteIds.includes(event.id);
      const isUpcoming = !event.event_date || new Date(event.event_date) >= now;
      return isFavorite && isUpcoming;
    });

  } catch (error) {
    console.error('Ошибка загрузки избранного:', error);
  } finally {
    loading.value = false;
  }
}

function removeFavorite(eventId) {
  const userId = authStore.userId;
  if (!userId) return;

  const stored = localStorage.getItem(`fav_${userId}`);
  const favs = stored ? JSON.parse(stored) : [];

  const index = favs.indexOf(eventId);
  if (index > -1) {
    favs.splice(index, 1);
  }

  localStorage.setItem(`fav_${userId}`, JSON.stringify(favs));

  // Удаляем из отображаемого списка
  favoriteEvents.value = favoriteEvents.value.filter(e => e.id !== eventId);

  // Оповещаем другие компоненты
  window.dispatchEvent(new Event('favoritesUpdated'));
}

onMounted(() => {
  loadFavorites();
  window.addEventListener('favoritesUpdated', loadFavorites);
});

onUnmounted(() => {
  window.removeEventListener('favoritesUpdated', loadFavorites);
});
</script>

<style scoped>
.section-subtitle {
  font-size: 16px;
  color: #777;
  margin-bottom: 28px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.event-card {
  border: 3px solid #ddd;
  border-radius: 14px;
  overflow: hidden;
  transition: transform 0.2s, border-color 0.2s;
}

.event-card:hover {
  transform: translateY(-3px);
  border-color: #ff4b12;
}

.card-image {
  height: 200px;
  overflow: hidden;
  cursor: pointer;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-card-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff6b35 0%, #e65c00 100%);
}

.card-body {
  padding: 18px;
}

.card-body h3 {
  font-size: 18px;
  margin-bottom: 10px;
  line-height: 1.3;
  cursor: pointer;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  font-size: 13px;
  color: #777;
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 10px;
}

.remove-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  background: none;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 13px;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Playfair Display', serif;
}

.remove-btn:hover {
  border-color: #dc3545;
  color: #dc3545;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #999;
}

.empty-state p {
  font-size: 18px;
  margin: 16px 0 24px;
}

.catalog-link {
  display: inline-block;
  padding: 14px 36px;
  background: #ff4b12;
  color: white;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  text-decoration: none;
  font-family: 'Playfair Display', serif;
  transition: background 0.2s;
}

.catalog-link:hover {
  background: #e04410;
}

.text-center { text-align: center; }
.py-5 { padding: 40px 0; }

@media (max-width: 900px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .cards { grid-template-columns: 1fr; }
}
</style>