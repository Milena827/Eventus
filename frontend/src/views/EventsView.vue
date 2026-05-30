<template>
  <div class="main">
    <h1>Каталог мероприятий</h1>

    <div v-if="loading" class="text-center py-5">Загрузка...</div>
    <section v-else class="cards">
      <div class="event-card" v-for="e in filteredEvents" :key="e.id" @click="$router.push(`/events/${e.id}`)">
        <div class="card-image">
          <img v-if="e.image_url && e.image_url.startsWith('http')" :src="e.image_url" :alt="e.title" />
          <div v-else class="no-card-image">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
            </svg>
          </div>
        </div>
        <div class="card-body">
          <h3>{{ e.title }}</h3>
          <div class="card-meta">
            <div v-if="e.event_date">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              {{ formatDate(e.event_date) }}
            </div>
            <div v-else>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              Дата уточняется
            </div>
            <div v-if="e.price_type">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              {{ e.price_type === 'free' ? 'Бесплатно' : e.price ? 'от ' + e.price + ' ₽' : 'Платно' }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="!loading && !filteredEvents.length" class="text-center py-5 text-muted">
      Актуальных мероприятий пока нет
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { eventsService } from '../services/eventsService';
import { formatDate } from '../utils/dateFormatter';

const allEvents = ref([]);
const loading = ref(true);

const filteredEvents = computed(() => {
  const now = new Date(); now.setHours(0,0,0,0);
  return allEvents.value.filter(e => !e.event_date || new Date(e.event_date) >= now);
});

onMounted(async () => {
  try { allEvents.value = await eventsService.getEvents({ limit: 100 }); }
  catch (err) { console.error(err); }
  finally { loading.value = false; }
});
</script>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.event-card {
  border: 3px solid #ddd;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
}

.event-card:hover {
  transform: translateY(-3px);
  border-color: #ff4b12;
}

.card-image {
  height: 200px;
  overflow: hidden;
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
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  font-size: 13px;
  color: #777;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-meta div {
  display: flex;
  align-items: center;
  gap: 5px;
}

@media (max-width: 900px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .cards { grid-template-columns: 1fr; }
}
</style>