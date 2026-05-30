<template>
  <div class="main">
    <h1>Моя лента</h1>

    <div v-if="loading" class="text-center py-5">Загрузка...</div>
    <div v-else-if="!authStore.isLoggedIn" class="text-center py-5">
      <p>Войдите в систему</p>
      <button class="login-btn" @click="$router.push('/login')">Войти</button>
    </div>
    <div v-else>
      <!-- Подборка 1: Компетенции -->
      <section class="feed-section" v-if="competenceEvents.length">
        <h2 class="section-title">Будет вам полезно</h2>
        <p class="section-subtitle">Мероприятия, которые помогут развить ваши компетенции</p>

        <button class="scroll-arrow scroll-left" @click="scrollComp(-1)" :disabled="compAtStart">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
        </button>

        <div class="scroll-wrapper">
          <div class="scroll-track" ref="compTrack" @scroll="onCompScroll">
            <div class="scroll-cards">
              <div class="scroll-card" v-for="(e, idx) in infiniteCompetenceEvents" :key="`comp-${idx}`" @click="$router.push(`/events/${e.id}`)">
                <div class="scroll-card-img">
                  <img v-if="e.image_url && e.image_url.startsWith('http')" :src="e.image_url" :alt="e.title" />
                  <div v-else class="no-scroll-img">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5">
                      <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
                    </svg>
                  </div>
                </div>
                <div class="scroll-card-body">
                  <h4>{{ e.title }}</h4>
                  <p class="scroll-card-meta" v-if="e.event_date">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    {{ formatDate(e.event_date) }}
                  </p>
                  <p class="scroll-card-meta" v-if="e.competence_name">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                    {{ e.competence_name }}
                  </p>
                  <!-- Тултип -->
                  <div class="scroll-tooltip" v-if="getTooltip(e)">{{ getTooltip(e) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <button class="scroll-arrow scroll-right" @click="scrollComp(1)" :disabled="compAtEnd">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </section>

      <div v-if="!competenceEvents.length" class="empty-feed">
        <p>Загрузите баллы тестирования в <router-link to="/profile">профиле</router-link></p>
      </div>

      <!-- Подборка 2: Интересы -->
      <section class="feed-section" v-if="interestEvents.length">
        <h2 class="section-title">Будет вам интересно</h2>
        <p class="section-subtitle">Мероприятия, подобранные по вашим интересам</p>

        <button class="scroll-arrow scroll-left" @click="scrollInt(-1)" :disabled="intAtStart">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
        </button>

        <div class="scroll-wrapper">
          <div class="scroll-track" ref="intTrack" @scroll="onIntScroll">
            <div class="scroll-cards">
              <div class="scroll-card" v-for="(e, idx) in infiniteInterestEvents" :key="`int-${idx}`" @click="$router.push(`/events/${e.id}`)">
                <div class="scroll-card-img">
                  <img v-if="e.image_url && e.image_url.startsWith('http')" :src="e.image_url" :alt="e.title" />
                  <div v-else class="no-scroll-img">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5">
                      <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
                    </svg>
                  </div>
                </div>
                <div class="scroll-card-body">
                  <h4>{{ e.title }}</h4>
                  <p class="scroll-card-meta" v-if="e.event_date">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    {{ formatDate(e.event_date) }}
                  </p>
                  <p class="scroll-card-meta" v-if="e.interest_name">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                    {{ e.interest_name }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <button class="scroll-arrow scroll-right" @click="scrollInt(1)" :disabled="intAtEnd">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </section>

      <div v-if="!interestEvents.length" class="empty-feed">
        <p>Выберите интересы в <router-link to="/profile">профиле</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import { useAuthStore } from '../stores/authStore';
import { recommendationsService } from '../services/recommendationsService';
import { formatDate } from '../utils/dateFormatter';

const authStore = useAuthStore();
const competenceEvents = ref([]);
const interestEvents = ref([]);
const loading = ref(true);

const compTrack = ref(null);
const intTrack = ref(null);
const compAtStart = ref(true);
const compAtEnd = ref(false);
const intAtStart = ref(true);
const intAtEnd = ref(false);

const infiniteCompetenceEvents = computed(() => {
  const arr = competenceEvents.value;
  return arr.length ? [...arr, ...arr, ...arr] : [];
});

const infiniteInterestEvents = computed(() => {
  const arr = interestEvents.value;
  return arr.length ? [...arr, ...arr, ...arr] : [];
});

function updateScrollState(track, atStart, atEnd) {
  if (!track) return;
  atStart.value = track.scrollLeft <= 5;
  atEnd.value = track.scrollLeft >= track.scrollWidth - track.clientWidth - 5;
}

function onCompScroll() { updateScrollState(compTrack.value, compAtStart, compAtEnd); }
function onIntScroll() { updateScrollState(intTrack.value, intAtStart, intAtEnd); }

function scrollComp(dir) {
  compTrack.value?.scrollBy({ left: 320 * dir, behavior: 'smooth' });
  setTimeout(() => updateScrollState(compTrack.value, compAtStart, compAtEnd), 400);
}

function scrollInt(dir) {
  intTrack.value?.scrollBy({ left: 320 * dir, behavior: 'smooth' });
  setTimeout(() => updateScrollState(intTrack.value, intAtStart, intAtEnd), 400);
}

function getTooltip(event) {
  if (event.adjacent_text) return event.adjacent_text;
  const s = event.competence_score, r = event.relevance, n = event.competence_name || 'компетенцию';
  if (s && s < 400) return `Низкий балл по «${n}» (${s}/800) — подтяните!`;
  if (r && r >= 4) return `Отлично развивает «${n}» (${r}/5)!`;
  if (r) return `Поможет развить «${n}» (${r}/5)`;
  return '';
}

onMounted(async () => {
  if (!authStore.userId) { loading.value = false; return; }
  try {
    const data = await recommendationsService.getRecommendations(authStore.userId);
    const now = new Date(); now.setHours(0,0,0,0);
    competenceEvents.value = (data.competence_based || []).filter(e => !e.event_date || new Date(e.event_date) >= now);
    interestEvents.value = (data.interest_based || []).filter(e => !e.event_date || new Date(e.event_date) >= now);

    await nextTick();
    if (compTrack.value && competenceEvents.value.length) {
      const cards = compTrack.value.querySelector('.scroll-cards');
      const mid = cards?.children[competenceEvents.value.length];
      if (mid) compTrack.value.scrollLeft = mid.offsetLeft;
      updateScrollState(compTrack.value, compAtStart, compAtEnd);
    }
    if (intTrack.value && interestEvents.value.length) {
      const cards = intTrack.value.querySelector('.scroll-cards');
      const mid = cards?.children[interestEvents.value.length];
      if (mid) intTrack.value.scrollLeft = mid.offsetLeft;
      updateScrollState(intTrack.value, intAtStart, intAtEnd);
    }
  } catch (err) { console.error(err); }
  finally { loading.value = false; }
});
</script>

<style scoped>
.main { padding-top: 10px; }
h1 { margin-bottom: 30px; }

.feed-section { margin-bottom: 60px; position: relative; }
.section-title { font-size: 36px; margin-bottom: 6px; }
.section-subtitle { font-size: 18px; color: #777; margin-bottom: 24px; }

.scroll-arrow {
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 36px; height: 36px;
  border: 2px solid #ddd; border-radius: 50%;
  background: white;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.2s; color: #666; z-index: 5;
}
.scroll-left { left: -48px; }
.scroll-right { right: -48px; }
.scroll-arrow:hover:not(:disabled) { border-color: #ff4b12; color: #ff4b12; }
.scroll-arrow:disabled { opacity: 0.2; cursor: default; }

.scroll-wrapper { width: 100%; }
.scroll-track { width: 100%; overflow-x: auto; scroll-behavior: smooth; scrollbar-width: none; -ms-overflow-style: none; }
.scroll-track::-webkit-scrollbar { display: none; }

.scroll-cards { display: flex; gap: 20px; }

.scroll-card {
  min-width: 300px; max-width: 300px; width: 300px;
  border: 3px solid #ddd; border-radius: 14px; overflow: hidden;
  cursor: pointer; transition: transform 0.2s, border-color 0.2s;
  position: relative; flex-shrink: 0;
}
.scroll-card:hover { transform: translateY(-3px); border-color: #ff4b12; }
.scroll-card-img { height: 180px; overflow: hidden; }
.scroll-card-img img { width: 100%; height: 100%; object-fit: cover; }

.no-scroll-img {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #ff6b35 0%, #e65c00 100%);
}

.scroll-card-body { padding: 14px; position: relative; }
.scroll-card-body h4 {
  font-size: 16px; margin-bottom: 6px; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.scroll-card-meta { font-size: 13px; color: #777; display: flex; align-items: center; gap: 4px; margin: 4px 0; }
.scroll-card-meta svg { flex-shrink: 0; }

/* Тултип */
.scroll-tooltip {
  opacity: 0; visibility: hidden;
  position: absolute; bottom: calc(100% + 8px); left: 10px; right: 10px;
  background: #1a1a1a; color: #fff; padding: 8px 12px; border-radius: 6px;
  font-size: 12px; line-height: 1.3; pointer-events: none;
  transition: opacity 0.2s, visibility 0.2s; z-index: 20;
  text-align: center;
}
.scroll-card:hover .scroll-tooltip { opacity: 1; visibility: visible; }

.empty-feed { text-align: center; padding: 30px; color: #777; font-size: 16px; }
.empty-feed a { color: #ff4b12; font-weight: 700; }

@media (max-width: 768px) {
  .scroll-card { min-width: 250px; max-width: 250px; width: 250px; }
  .section-title { font-size: 28px; }
  .scroll-arrow { width: 28px; height: 28px; }
  .scroll-left { left: -38px; }
  .scroll-right { right: -38px; }
}
</style>