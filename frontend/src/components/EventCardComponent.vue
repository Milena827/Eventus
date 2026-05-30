<template>
  <div class="event-card" @click="$router.push(`/events/${event.id}`)">
    <div class="card-image">
      <img v-if="event.image_url && event.image_url.startsWith('http')" :src="event.image_url" :alt="event.title" />
      <div v-else class="no-image">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
      </div>
      <button
        class="favorite-btn"
        :class="{ active: isFavorite }"
        @click.stop="toggleFavorite"
        :title="isFavorite ? 'Убрать из избранного' : 'Добавить в избранное'"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" :fill="isFavorite ? '#000' : 'none'" stroke="currentColor" stroke-width="2">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
      </button>
    </div>
    <h3>{{ event.title }}</h3>
    <div class="event-meta">
      <div v-if="event.event_date">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        {{ formatDate(event.event_date) }}
      </div>
      <div v-else>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        Дата уточняется
      </div>
      <div>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        {{ cleanLocation(event.location) }}
      </div>
      <div v-if="event.price_type && event.price_type !== 'None'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        {{ event.price_type === 'free' ? 'Бесплатно' : event.price ? 'от ' + event.price + ' ₽' : 'Платно' }}
      </div>
    </div>
    <div v-if="showTooltip && recommendationReason" class="tooltip-reason">{{ recommendationReason }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { formatDate } from '../utils/dateFormatter';
import { useAuthStore } from '../stores/authStore';

const props = defineProps({
  event: { type: Object, required: true },
  type: { type: String, default: '' },
  showTooltip: { type: Boolean, default: false }
});

const authStore = useAuthStore();
const isFavorite = ref(false);

// Загружаем статус избранного
function checkFavorite() {
  if (!authStore.userId) {
    isFavorite.value = false;
    return;
  }
  const stored = localStorage.getItem(`fav_${authStore.userId}`);
  const favs = stored ? JSON.parse(stored) : [];
  isFavorite.value = favs.includes(props.event.id);
}

onMounted(() => {
  checkFavorite();
  window.addEventListener('favoritesUpdated', checkFavorite);
});

// Следим за изменением события
watch(() => props.event.id, () => {
  checkFavorite();
});

function toggleFavorite() {
  if (!authStore.userId) return;

  const stored = localStorage.getItem(`fav_${authStore.userId}`);
  const favs = stored ? JSON.parse(stored) : [];

  if (isFavorite.value) {
    // Удаляем из избранного
    const index = favs.indexOf(props.event.id);
    if (index > -1) {
      favs.splice(index, 1);
    }
  } else {
    // Добавляем в избранное
    if (!favs.includes(props.event.id)) {
      favs.push(props.event.id);
    }
  }

  // Сохраняем
  localStorage.setItem(`fav_${authStore.userId}`, JSON.stringify(favs));
  isFavorite.value = !isFavorite.value;

  // Оповещаем другие компоненты
  window.dispatchEvent(new Event('favoritesUpdated'));
}

const recommendationReason = computed(() => {
  if (!props.showTooltip) return '';

  const score = props.event.competence_score;
  const relevance = props.event.relevance;
  const compName = props.event.competence_name || 'компетенцию';

  if (score && score < 400) {
    return `У вас низкий балл по «${compName}» (${score}/800). Это мероприятие поможет!`;
  }
  if (relevance && relevance >= 4) {
    return `Отлично развивает «${compName}» (релевантность ${relevance}/5)!`;
  }
  if (relevance) {
    return `Поможет развить «${compName}» (релевантность ${relevance}/5).`;
  }
  if (props.type === 'interest') {
    return 'Подобрано по вашим интересам!';
  }
  return '';
});

function cleanLocation(loc) {
  if (!loc) return 'Тюмень';
  let t = String(loc);
  if (t.includes('cityAlias')) {
    try { return JSON.parse(t.replace(/'/g, '"')).text.replace(/xa0/g, ' ') || 'Тюмень'; }
    catch { return 'Тюмень'; }
  }
  return t.replace(/xa0/g, ' ');
}
</script>

<style scoped>
.event-card { position: relative; }

.favorite-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255,255,255,0.9);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
  z-index: 5;
}

.favorite-btn:hover,
.favorite-btn.active {
  color: #000;
  background: #fff;
}

.tooltip-reason {
  opacity: 0;
  visibility: hidden;
  position: absolute;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  background: #1a1a1a;
  color: #fff;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.4;
  pointer-events: none;
  transition: opacity 0.2s, visibility 0.2s;
  z-index: 100;
  max-width: 260px;
  white-space: normal;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
}

.tooltip-reason::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: #1a1a1a;
}

.event-card:hover .tooltip-reason {
  opacity: 1;
  visibility: visible;
}
</style>