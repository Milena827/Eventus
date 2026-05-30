<template>
  <div>
    <div v-if="loading" class="text-center py-5">Загрузка...</div>
    <div v-else-if="!authStore.isLoggedIn" class="text-center py-5">
      <p>Войдите в систему</p>
      <button class="login-btn" @click="$router.push('/login')">Войти</button>
    </div>
    <div v-else class="profile">
      <aside class="sidebar">
        <div class="avatar-card">
          <div class="avatar-head"></div>
          <div class="avatar-body"></div>
        </div>
        <button class="side-btn" @click="startEdit('competences')">
          {{ editMode.competences ? 'Закрыть' : 'Компетенции' }}
        </button>
        <button class="side-btn" @click="startEdit('interests')">
          {{ editMode.interests ? 'Закрыть' : 'Интересы' }}
        </button>
        <button class="side-btn danger" @click="handleLogout">Выход</button>
      </aside>

      <section class="content">
        <h1 class="profile-name">{{ profile.user.full_name }}</h1>
        <p class="profile-email">{{ profile.user.email }}</p>
        <p class="profile-meta">{{ profile.user.faculty }}, {{ profile.user.course }} курс</p>

        <!-- Сводка -->
        <div class="summary-card" v-if="profile.test_results?.length">
          <h3>Сводка компетенций</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <div class="summary-number low">{{ lowCount }}</div>
              <div class="summary-label">Зоны роста</div>
              <div class="summary-hint">Требуют развития</div>
            </div>
            <div class="summary-item">
              <div class="summary-number mid">{{ midCount }}</div>
              <div class="summary-label">Средний уровень</div>
              <div class="summary-hint">Можно улучшить</div>
            </div>
            <div class="summary-item">
              <div class="summary-number high">{{ highCount }}</div>
              <div class="summary-label">Сильные стороны</div>
              <div class="summary-hint">Ваши опоры</div>
            </div>
            <div class="summary-item">
              <div class="summary-number">{{ avgScore }}</div>
              <div class="summary-label">Средний балл</div>
              <div class="summary-hint">Из 800 возможных</div>
            </div>
          </div>
          <div class="summary-detail" v-if="topWeak.length">
            <p>Зоны роста: <strong>{{ topWeak.map(r => r.competence_name).join(', ') }}</strong></p>
          </div>
          <div class="summary-detail" v-if="topStrong.length">
            <p>Сильные стороны: <strong>{{ topStrong.map(r => r.competence_name).join(', ') }}</strong></p>
          </div>
        </div>

        <!-- Компетенции -->
        <h2>Компетенции</h2>

        <!-- Просмотр -->
        <div v-if="!editMode.competences">
          <div v-if="profile.test_results?.length" class="skills">
            <div v-for="r in profile.test_results" :key="r.competence_id">
              <div class="skill-row">
                <span>{{ r.competence_name }}</span>
                <span>{{ r.score }} / 800</span>
              </div>
              <div class="skill-bar">
                <div class="fill" :style="{width: (r.score/800*100)+'%', background: r.score<400?'#dc3545':r.score<600?'#ffc107':'#28a745'}"></div>
              </div>
            </div>
          </div>
          <p v-else class="text-muted">Баллы не загружены. Нажмите «Компетенции» в меню слева, чтобы добавить.</p>
        </div>

        <!-- Редактирование -->
        <div v-if="editMode.competences">
          <div v-for="c in competencesList" :key="c.id" class="form-group">
            <label class="form-label">{{ c.name }}</label>
            <input v-model.number="scores[c.id]" type="number" min="200" max="800" class="form-control" placeholder="200-800" />
          </div>
          <div class="edit-actions">
            <button class="save-btn" @click="saveTests" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
            <button class="cancel-btn" @click="cancelEdit('competences')">Отмена</button>
          </div>
          <p v-if="testMsg" :class="testOk ? 'alert alert-success mt-3' : 'alert alert-danger mt-3'">{{ testMsg }}</p>
        </div>

        <!-- Интересы -->
        <h2 class="mt-4">Интересы</h2>

        <!-- Просмотр -->
        <div v-if="!editMode.interests">
          <div v-if="profile.interests?.length">
            <div class="skill-row" v-for="i in profile.interests" :key="i.category_id">
              <span>{{ i.category_name }}</span>
            </div>
          </div>
          <p v-else class="text-muted">Интересы не выбраны. Нажмите «Интересы» в меню слева, чтобы выбрать.</p>
        </div>

        <!-- Редактирование -->
        <div v-if="editMode.interests">
          <div v-for="c in categoriesList" :key="c.id" class="form-group" style="display:flex;align-items:center;gap:10px;">
            <input type="checkbox" :value="c.id" v-model="selectedInterests" :id="'cat'+c.id" style="width:20px;height:20px;" />
            <label :for="'cat'+c.id" style="font-size:16px;">{{ c.name }}</label>
          </div>
          <div class="edit-actions">
            <button class="save-btn" @click="saveInterests" :disabled="saving">{{ saving ? 'Сохранение...' : 'Сохранить' }}</button>
            <button class="cancel-btn" @click="cancelEdit('interests')">Отмена</button>
          </div>
          <p v-if="intMsg" :class="intOk ? 'alert alert-success mt-3' : 'alert alert-danger mt-3'">{{ intMsg }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { userService } from '../services/userService';

const router = useRouter();
const authStore = useAuthStore();
const profile = ref({ user: {}, test_results: [], interests: [] });
const loading = ref(true);
const saving = ref(false);

const editMode = reactive({ competences: false, interests: false });
const scores = reactive({});
const selectedInterests = ref([]);
const testMsg = ref(''); const testOk = ref(false);
const intMsg = ref(''); const intOk = ref(false);

const competencesList = [
  { id: 1, name: 'Анализ информации' }, { id: 2, name: 'Планирование' }, { id: 3, name: 'Партнерство/сотрудничество' },
  { id: 4, name: 'Коммуникативная грамотность' }, { id: 5, name: 'Клиентоориентированность' }, { id: 6, name: 'Стрессоустойчивость' },
  { id: 7, name: 'Эмоциональный интеллект' }, { id: 8, name: 'Ориентация на результат' }, { id: 9, name: 'Саморазвитие' },
  { id: 10, name: 'Следование правилам' }, { id: 11, name: 'Лидерство' }
];

const categoriesList = [
  { id: 1, name: 'IT' }, { id: 2, name: 'Спорт' }, { id: 3, name: 'Наука' },
  { id: 4, name: 'Настольные игры' }, { id: 5, name: 'Музыка' }, { id: 6, name: 'Бизнес' }, { id: 7, name: 'Искусство' }
];

const lowCount = computed(() => profile.value.test_results?.filter(r => r.score < 400).length || 0);
const midCount = computed(() => profile.value.test_results?.filter(r => r.score >= 400 && r.score < 600).length || 0);
const highCount = computed(() => profile.value.test_results?.filter(r => r.score >= 600).length || 0);
const avgScore = computed(() => {
  const arr = profile.value.test_results;
  return arr?.length ? Math.round(arr.reduce((s, r) => s + r.score, 0) / arr.length) : 0;
});
const topWeak = computed(() => profile.value.test_results?.filter(r => r.score < 400).slice(0, 3) || []);
const topStrong = computed(() => profile.value.test_results?.filter(r => r.score >= 600).slice(0, 3) || []);

onMounted(async () => {
  if (!authStore.userId) { loading.value = false; return; }
  await loadProfile();
});

async function loadProfile() {
  try { profile.value = await userService.getFullProfile(authStore.userId); }
  catch (err) { console.error(err); }
  finally { loading.value = false; }
}

function startEdit(section) {
  if (section === 'competences') {
    if (editMode.competences) { editMode.competences = false; return; }
    Object.keys(scores).forEach(k => delete scores[k]);
    profile.value.test_results?.forEach(r => { scores[r.competence_id] = r.score; });
    testMsg.value = '';
    editMode.competences = true;
  }
  if (section === 'interests') {
    if (editMode.interests) { editMode.interests = false; return; }
    selectedInterests.value = (profile.value.interests || []).map(i => i.category_id);
    intMsg.value = '';
    editMode.interests = true;
  }
}

function cancelEdit(section) { editMode[section] = false; }

async function saveTests() {
  const results = Object.entries(scores).filter(([_,v]) => v>=200 && v<=800).map(([k,v])=>({competence_id:+k, score:v}));
  if (!results.length) { testMsg.value='Введите баллы (200-800)'; testOk.value=false; return; }
  saving.value = true;
  try {
    await userService.addTestResults(authStore.userId, results);
    testMsg.value='Сохранено! Переход в ленту...'; testOk.value=true;
    await loadProfile();
    setTimeout(()=>router.push('/feed'), 1500);
  } catch { testMsg.value='Ошибка'; testOk.value=false; }
  finally { saving.value=false; }
}

async function saveInterests() {
  if (!selectedInterests.value.length) { intMsg.value='Выберите категории'; intOk.value=false; return; }
  saving.value = true;
  try {
    await userService.addInterests(authStore.userId, selectedInterests.value.map(id=>({category_id:id, weight:1})));
    intMsg.value='Сохранено! Переход в ленту...'; intOk.value=true;
    await loadProfile();
    setTimeout(()=>router.push('/feed'), 1500);
  } catch { intMsg.value='Ошибка'; intOk.value=false; }
  finally { saving.value=false; }
}

function handleLogout() { authStore.logout(); router.push('/'); }
</script>

<style scoped>
.profile {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px 20px 120px;
  display: flex;
  gap: 24px;
}

.sidebar { width: 220px; flex-shrink: 0; }

.avatar-card {
  height: 220px;
  border: 3px solid #aaa;
  border-radius: 26px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

.avatar-head {
  width: 80px; height: 80px;
  border: 4px solid #ff4b12;
  border-radius: 50%;
  margin-bottom: 14px;
}

.avatar-body {
  width: 130px; height: 80px;
  border: 4px solid #ff4b12;
  border-top-left-radius: 65px; border-top-right-radius: 65px;
  border-bottom-left-radius: 30px; border-bottom-right-radius: 30px;
}

.side-btn {
  width: 100%; height: 40px; margin-top: 10px;
  border: 3px solid #aaa; border-radius: 12px; background: white;
  font-size: 16px; font-weight: 700;
  font-family: 'Playfair Display', serif; cursor: pointer;
  transition: border-color 0.2s;
}

.side-btn:hover { border-color: #ff4b12; }
.side-btn.danger { border-color: #aaa; color: #c00; }

.content { flex: 1; min-width: 0; }

.profile-name { font-size: 34px; margin: 0 0 4px; }
.profile-email { font-size: 15px; color: #777; margin: 0 0 4px; }
.profile-meta { font-size: 17px; color: #777; margin: 0 0 22px; }

/* Сводка */
.summary-card {
  border: 3px solid #ddd; border-radius: 16px; padding: 18px 22px;
  margin-bottom: 26px;
}

.summary-card h3 { font-size: 19px; margin-bottom: 14px; }

.summary-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  margin-bottom: 14px;
}

.summary-item { text-align: center; }

.summary-number {
  font-size: 30px; font-weight: 700; line-height: 1;
}

.summary-number.low { color: #dc3545; }
.summary-number.mid { color: #ffc107; }
.summary-number.high { color: #28a745; }

.summary-label { font-size: 12px; color: #333; margin-top: 3px; }
.summary-hint { font-size: 10px; color: #999; }

.summary-detail { font-size: 13px; color: #555; margin-top: 6px; line-height: 1.4; }

h2 { font-size: 20px; margin-bottom: 10px; }

.skills { width: 100%; }

.skill-row {
  height: 36px; border: 3px solid #aaa; border-radius: 10px;
  margin-bottom: 4px; padding: 0 16px;
  display: flex; align-items: center; justify-content: space-between;
  color: #777; font-size: 16px; font-weight: 700;
}

.skill-bar {
  height: 5px; border-radius: 3px; margin: 2px 0 12px; background: #eee;
}

.skill-bar .fill { height: 100%; border-radius: 3px; }

.form-group { margin-bottom: 8px; }

.form-label { display: block; font-size: 13px; font-weight: 700; margin-bottom: 3px; }

.form-control {
  width: 100%; padding: 8px 12px; border: 3px solid #aaa; border-radius: 10px;
  font-size: 15px; font-family: 'Playfair Display', serif;
}

.form-control:focus { outline: none; border-color: #ff4b12; }

/* Кнопки редактирования */
.edit-actions {
  display: flex; gap: 12px; margin-top: 16px;
}

.save-btn {
  padding: 10px 24px;
  background: #ff4b12;
  color: white;
  border: none; border-radius: 6px;
  font-size: 15px; font-family: 'Playfair Display', serif;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover:not(:disabled) { background: #e04410; }
.save-btn:disabled { opacity: 0.5; cursor: default; }

.cancel-btn {
  padding: 10px 24px;
  background: #eee;
  color: #333;
  border: none; border-radius: 6px;
  font-size: 15px; font-family: 'Playfair Display', serif;
  cursor: pointer;
  transition: background 0.2s;
}

.cancel-btn:hover { background: #ddd; }

.alert { padding: 8px 12px; border-radius: 8px; font-size: 13px; }
.alert-success { background: #e0ffe0; color: #060; }
.alert-danger { background: #ffe0e0; color: #900; }

.text-muted { color: #999; font-size: 14px; }
.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 18px; }

@media (max-width: 768px) {
  .profile { flex-direction: column; }
  .sidebar { width: 100%; }
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
  .profile-name { font-size: 26px; }
}
</style>