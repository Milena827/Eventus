<template>
  <div class="main">
    <h1>Ближайшие мероприятия</h1>

    <section class="main-event" v-if="featuredEvent">
      <div class="hero-image">
        <img v-if="featuredEvent.image_url && featuredEvent.image_url.startsWith('http')" :src="featuredEvent.image_url" :alt="featuredEvent.title" />
        <div v-else class="no-hero-img">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="#aaa" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
          </svg>
        </div>
      </div>
      <div class="event-info">
        <h2>{{ featuredEvent.title }}</h2>
        <p>{{ truncate(featuredEvent.description, 300) }}</p>
        <router-link :to="`/events/${featuredEvent.id}`" class="primary-btn">Перейти</router-link>
      </div>
    </section>

    <section class="cards">
      <div class="event-card" v-for="e in events" :key="e.id" @click="$router.push(`/events/${e.id}`)">
        <div class="card-image">
          <img v-if="e.image_url && e.image_url.startsWith('http')" :src="e.image_url" :alt="e.title" />
          <div v-else class="no-image">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
            </svg>
          </div>
        </div>
        <h3>{{ e.title }}</h3>
        <div class="event-meta">
          <div v-if="e.event_date">📅 {{ formatDate(e.event_date) }}</div>
        </div>
      </div>
    </section>

    <div v-if="loading" class="text-center py-5">Загрузка...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { eventsService } from '../services/eventsService';
import { formatDate } from '../utils/dateFormatter';

const allEvents = ref([]);
const loading = ref(true);

const filtered = computed(() => {
  const now = new Date(); now.setHours(0,0,0,0);
  return allEvents.value.filter(e => !e.event_date || new Date(e.event_date) >= now);
});

const featuredEvent = computed(() => filtered.value[0] || null);
const events = computed(() => filtered.value.slice(1, 50));

function truncate(text, max) { return text?.length > max ? text.substring(0, max) + '...' : text || ''; }

onMounted(async () => {
  try { allEvents.value = await eventsService.getEvents({ limit: 500 }); }
  catch (err) { console.error(err); }
  finally { loading.value = false; }
});
</script>