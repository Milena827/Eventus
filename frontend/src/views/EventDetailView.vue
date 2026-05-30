<template>
  <div class="main">
    <div v-if="loading" class="text-center py-5">Загрузка...</div>
    <div v-else-if="event">
      <div class="breadcrumb">
        <router-link to="/events">Каталог</router-link>
        <span>/</span>
        <span>{{ event.title }}</span>
      </div>

      <div class="detail-grid">
        <!-- Изображение -->
        <div class="detail-image-wrapper">
          <div class="detail-image" v-if="event.image_url && event.image_url.startsWith('http')">
            <img :src="event.image_url" :alt="event.title" />
          </div>
          <div v-else class="no-detail-image">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
            </svg>
          </div>
        </div>

        <!-- Информация -->
        <div class="detail-info">
          <h2>{{ event.title }}</h2>

          <div class="detail-meta">
            <div class="meta-row">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              <span v-if="event.event_date">{{ formatDateTime(event.event_date) }}</span>
              <span v-else>Дата уточняется</span>
            </div>
            <div class="meta-row">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              <span>{{ cleanLocation(event.location) }}</span>
            </div>
            <div class="meta-row" v-if="event.format">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              <span>{{ event.format === 'online' ? 'Онлайн' : 'Офлайн' }}</span>
            </div>
            <div class="meta-row" v-if="event.price_type && event.price_type !== 'None'">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              <span v-if="event.price_type === 'free'" class="free-badge">Бесплатно</span>
              <span v-else>{{ event.price ? event.price + ' ₽' : 'Платно' }}</span>
            </div>
          </div>

          <div v-if="event.competences?.length" class="detail-tags">
            <h4>Компетенции</h4>
            <div class="tags-list">
              <span v-for="c in event.competences" :key="c.id" class="tag-item">{{ c.name }} <small>({{ c.relevance }}/5)</small></span>
            </div>
          </div>

          <div v-if="event.categories?.length" class="detail-tags">
            <h4>Категории</h4>
            <div class="tags-list">
              <span v-for="c in event.categories" :key="c.id" class="tag-item category-tag">{{ c.name }}</span>
            </div>
          </div>

          <!-- Кнопки -->
          <div class="detail-actions" v-if="authStore.isLoggedIn">
            <button class="action-btn" :class="{ active: goingActive }" @click="handleAction('going')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              {{ goingActive ? '✓ Иду!' : 'Пойду' }}
            </button>
            <button class="action-btn" :class="{ active: isFavorite }" @click="toggleFavorite">
              <svg width="16" height="16" viewBox="0 0 24 24" :fill="isFavorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              {{ isFavorite ? 'В избранном' : 'В избранное' }}
            </button>
          </div>

          <a v-if="event.url" :href="event.url" target="_blank" class="source-link">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            Источник
          </a>

          <!-- Оценка -->
          <div class="rating-section" v-if="authStore.isLoggedIn">
            <h4>Оценить</h4>
            <div class="stars">
              <button v-for="s in 5" :key="s" class="star-btn" :class="{ active: userRating >= s }" @click="handleRating(s)">
                <svg width="28" height="28" viewBox="0 0 24 24" :fill="userRating >= s ? '#ff4b12' : 'none'" stroke="#ff4b12" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              </button>
              <span v-if="userRating" class="rating-text">{{ ratingLabels[userRating] }}</span>
              <span v-if="avgRating > 0" class="avg-text">(Средняя: {{ avgRating.toFixed(1) }})</span>
            </div>
            <p v-if="ratingMsg" class="msg-success">{{ ratingMsg }}</p>
          </div>

          <!-- Отзыв -->
          <div class="review-section" v-if="authStore.isLoggedIn">
            <h4>Оставить отзыв</h4>
            <textarea v-model="reviewText" class="review-input" placeholder="Поделитесь впечатлениями..." rows="3"></textarea>
            <button class="action-btn" @click="handleReview" :disabled="!reviewText.trim()" style="margin-top:8px;">Отправить</button>
            <p v-if="reviewMsg" :class="reviewOk ? 'msg-success' : 'msg-error'">{{ reviewMsg }}</p>

            <div class="reviews-list" v-if="textReviews.length">
              <div v-for="(r, i) in textReviews" :key="i" class="review-item">
                <div class="review-header"><span class="review-date">{{ formatDateTime(r.created_at) }}</span></div>
                <p class="review-text">{{ r.review_text }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-description" v-if="event.description">
        <h3>Описание</h3>
        <p>{{ event.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { eventsService } from '../services/eventsService';
import { recommendationsService } from '../services/recommendationsService';
import { formatDateTime } from '../utils/dateFormatter';

const route = useRoute();
const authStore = useAuthStore();
const event = ref(null);
const loading = ref(true);
const isFavorite = ref(false);
const goingActive = ref(false);
const userRating = ref(0);
const ratingMsg = ref('');
const reviewText = ref('');
const reviewMsg = ref('');
const reviewOk = ref(false);
const allReviews = ref([]);

const ratingLabels = ['', 'Ужасно', 'Плохо', 'Нормально', 'Хорошо', 'Отлично'];
const avgRating = computed(() => {
  const ratings = allReviews.value.filter(r => r.rating).map(r => r.rating);
  return ratings.length ? ratings.reduce((s, r) => s + r, 0) / ratings.length : 0;
});
const textReviews = computed(() => allReviews.value.filter(r => r.review_text));

function cleanLocation(loc) {
  if (!loc) return 'Тюмень';
  let t = String(loc);
  if (t.includes('cityAlias')) {
    try { return JSON.parse(t.replace(/'/g, '"')).text?.replace(/xa0/g, ' ') || 'Тюмень'; }
    catch { return 'Тюмень'; }
  }
  return t.replace(/xa0/g, ' ');
}

function checkFavorite() {
  if (!authStore.userId || !event.value) return;
  const favs = JSON.parse(localStorage.getItem(`fav_${authStore.userId}`) || '[]');
  isFavorite.value = favs.includes(event.value.id);
}

function toggleFavorite() {
  if (!authStore.userId || !event.value) return;
  const favs = JSON.parse(localStorage.getItem(`fav_${authStore.userId}`) || '[]');
  if (isFavorite.value) {
    const i = favs.indexOf(event.value.id);
    if (i > -1) favs.splice(i, 1);
  } else {
    favs.push(event.value.id);
  }
  localStorage.setItem(`fav_${authStore.userId}`, JSON.stringify(favs));
  isFavorite.value = !isFavorite.value;
  window.dispatchEvent(new Event('favoritesUpdated'));
}

async function handleAction(type) {
  if (!event.value) return;
  try {
    await recommendationsService.addAction(authStore.userId, { event_id: event.value.id, action_type: type });
    if (type === 'going') { goingActive.value = true; setTimeout(() => goingActive.value = false, 3000); }
  } catch (e) { console.error(e); }
}

async function handleRating(star) {
  if (!event.value) return;
  userRating.value = star;
  ratingMsg.value = '';
  try {
    await recommendationsService.addAction(authStore.userId, { event_id: event.value.id, action_type: 'rate', rating: star });
    ratingMsg.value = 'Оценка сохранена!';
    await loadReviews();
    setTimeout(() => ratingMsg.value = '', 2000);
  } catch (e) { console.error(e); }
}

async function handleReview() {
  if (!reviewText.value.trim() || !event.value) return;
  try {
    await recommendationsService.addAction(authStore.userId, { event_id: event.value.id, action_type: 'rate', review_text: reviewText.value.trim() });
    reviewMsg.value = 'Отзыв отправлен!';
    reviewOk.value = true;
    reviewText.value = '';
    await loadReviews();
    setTimeout(() => reviewMsg.value = '', 3000);
  } catch (e) { reviewMsg.value = 'Ошибка'; reviewOk.value = false; }
}

async function loadReviews() {
  if (!authStore.userId || !event.value) return;
  try {
    const actions = await recommendationsService.getActions(authStore.userId);
    allReviews.value = actions.filter(a => a.event_id === event.value.id && (a.review_text || a.rating));
  } catch (e) { console.error(e); }
}

onMounted(async () => {
  try {
    event.value = await eventsService.getEvent(route.params.id);
    checkFavorite();
    await loadReviews();
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
});

watch(() => route.params.id, async () => {
  loading.value = true;
  try {
    event.value = await eventsService.getEvent(route.params.id);
    checkFavorite();
    await loadReviews();
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
});
</script>

<style scoped>
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 50px; }
.detail-image-wrapper { align-self: start; }
.detail-image { border-radius: 14px; overflow: hidden; }
.detail-image img { width: 100%; height: auto; display: block; border-radius: 14px; }
.no-detail-image {
  width: 100%; min-height: 250px; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ff6b35 0%, #e65c00 100%); border-radius: 14px;
}
.detail-info h2 { font-size: 34px; margin-bottom: 24px; line-height: 1.2; }
.detail-meta { display: flex; flex-direction: column; gap: 14px; margin-bottom: 28px; }
.meta-row { display: flex; align-items: center; gap: 10px; font-size: 18px; color: #333; }
.free-badge { color: #28a745; font-weight: 700; }
.detail-tags { margin-bottom: 20px; }
.detail-tags h4 { font-size: 20px; margin-bottom: 10px; }
.tags-list { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-item {
  display: inline-block; border: 2px solid #ff4b12; border-radius: 10px;
  padding: 6px 14px; font-size: 14px; font-weight: 700; color: #ff4b12;
}
.tag-item small { font-weight: 400; color: #999; }
.category-tag { border-color: #08a8e8; color: #08a8e8; }
.detail-actions { display: flex; gap: 12px; margin-top: 24px; flex-wrap: wrap; }
.action-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 24px; border: 3px solid #ddd; border-radius: 10px;
  background: white; font-size: 16px; cursor: pointer;
  font-family: 'Playfair Display', serif; transition: all 0.2s; color: #333;
}
.action-btn:hover { border-color: #ff4b12; }
.action-btn.active { background: #ff4b12; color: white; border-color: #ff4b12; }
.source-link {
  display: inline-flex; align-items: center; gap: 8px;
  margin-top: 16px; padding: 12px 24px; border: 3px solid #ddd; border-radius: 10px;
  text-decoration: none; color: #333; font-size: 16px; transition: border-color 0.2s;
}
.source-link:hover { border-color: #ff4b12; }
.rating-section { margin-top: 24px; }
.rating-section h4 { font-size: 20px; margin-bottom: 8px; }
.stars { display: flex; align-items: center; gap: 4px; }
.star-btn { background: none; border: none; cursor: pointer; padding: 0; transition: transform 0.2s; }
.star-btn:hover { transform: scale(1.15); }
.rating-text { font-size: 16px; color: #ff4b12; margin-left: 10px; font-weight: 700; }
.avg-text { font-size: 14px; color: #999; margin-left: 10px; }
.msg-success { color: #28a745; margin-top: 8px; font-size: 14px; }
.msg-error { color: #dc3545; margin-top: 8px; font-size: 14px; }
.review-section { margin-top: 20px; }
.review-section h4 { font-size: 20px; margin-bottom: 8px; }
.review-input {
  width: 100%; padding: 12px; border: 3px solid #ddd; border-radius: 10px;
  font-size: 16px; font-family: 'Playfair Display', serif; resize: vertical;
}
.review-input:focus { outline: none; border-color: #ff4b12; }
.reviews-list { margin-top: 20px; }
.review-item { border: 2px solid #ddd; border-radius: 10px; padding: 14px; margin-bottom: 10px; }
.review-header { display: flex; justify-content: space-between; font-size: 13px; color: #999; margin-bottom: 6px; }
.review-text { font-size: 16px; color: #333; line-height: 1.4; }
.detail-description { margin-top: 40px; }
.detail-description h3 { font-size: 24px; margin-bottom: 16px; }
.detail-description p { font-size: 18px; line-height: 1.6; color: #333; white-space: pre-line; }
@media (max-width: 768px) { .detail-grid { grid-template-columns: 1fr; } .detail-info h2 { font-size: 26px; } }
</style>