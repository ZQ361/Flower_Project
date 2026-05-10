<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import AuthPanel from "./components/AuthPanel.vue";
import CatalogPanel from "./components/CatalogPanel.vue";
import HistorySidebar from "./components/HistorySidebar.vue";
import RagPanel from "./components/RagPanel.vue";
import ResultCard from "./components/ResultCard.vue";
import UploadPanel from "./components/UploadPanel.vue";
import {
  addFavorite,
  checkHealth,
  deleteRagSession,
  fetchFavorites,
  fetchHistory,
  fetchPlants,
  fetchRagSessionDetail,
  fetchRagSessions,
  login,
  predictFlower,
  register,
  removeFavorite,
  removeHistory,
  sendRagChatStream,
} from "./lib/api";
import {
  clearAuthSession,
  formatConfidence,
  getAuthUser,
  setAuthSession,
  toFavoriteStackItem,
  toHistoryStackItem,
} from "./lib/storage";

const backendStatus = ref("后端检查中...");
const backendKind = ref("");
const currentFile = ref(null);
const previewUrl = ref("");
const catalog = ref([]);
const catalogQuery = ref("");
const catalogImages = ref({});
const plantNames = ref({});
const selectedResult = ref(null);
const loadingPredict = ref(false);
const loadingCatalog = ref(false);
const authLoading = ref(false);
const authError = ref("");
const currentUser = ref(null);
const authToken = ref("");
const favorites = ref([]);
const history = ref([]);
const ragSessions = ref([]);
const activeRagSessionId = ref(null);
const ragCurrentPlant = ref(null);
const ragSessionTitle = ref("花卉问答");
const ragMessages = ref([]);
const ragLoading = ref(false);
const ragError = ref("");
const pageMode = ref("auth");
const accessMode = ref("user");
const activeView = ref("recognition");

const previewFileName = computed(() => {
  if (!currentFile.value) return "未选择图片";
  const sizeMb = (currentFile.value.size / 1024 / 1024).toFixed(2);
  return `${currentFile.value.name} · ${sizeMb} MB`;
});

const isLoggedIn = computed(() => Boolean(authToken.value && currentUser.value));
const canUseCloudRecords = computed(() => pageMode.value === "app" && isLoggedIn.value);
const selectedPlant = computed(() => selectedResult.value?.plant || null);
const ragFocusPlant = computed(() => ragCurrentPlant.value || selectedPlant.value || null);
const ragDisplayTitle = computed(() => {
  if (ragSessionTitle.value) return ragSessionTitle.value;
  if (ragFocusPlant.value?.display_name) return `${ragFocusPlant.value.display_name} 问答`;
  return "花卉问答";
});
const catalogWithImages = computed(() =>
  catalog.value.map((item) => ({
    ...item,
    image_url: catalogImages.value[item.class_id] || "",
  }))
);
const selectedResultWithChineseTop3 = computed(() => {
  if (!selectedResult.value) return null;
  return {
    ...selectedResult.value,
    top3: (selectedResult.value.top3 || []).map((item) => ({
      ...item,
      display_name: plantNames.value[item.class_id] || item.display_name || item.class_name,
    })),
  };
});

function setSession(token, user) {
  authToken.value = token;
  currentUser.value = user;
  setAuthSession(token, user);
  accessMode.value = "user";
}

function resetRagState() {
  ragSessions.value = [];
  activeRagSessionId.value = null;
  ragCurrentPlant.value = null;
  ragSessionTitle.value = "花卉问答";
  ragMessages.value = [];
  ragLoading.value = false;
  ragError.value = "";
}

function clearSession() {
  authToken.value = "";
  currentUser.value = null;
  clearAuthSession();
  favorites.value = [];
  history.value = [];
  resetRagState();
}

function enterApp(mode = "user") {
  accessMode.value = mode;
  pageMode.value = "app";
  activeView.value = "recognition";
  if (mode === "guest") {
    clearSession();
    pageMode.value = "app";
    accessMode.value = "guest";
  }
}

function exitToAuthPage() {
  pageMode.value = "auth";
  accessMode.value = "user";
  activeView.value = "recognition";
  currentFile.value = null;
  selectedResult.value = null;
  ragCurrentPlant.value = null;
  ragSessionTitle.value = "花卉问答";
  ragMessages.value = [];
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = "";
  }
}

function normalizeResult(result) {
  if (!result) return null;
  return {
    ...result,
    top3: Array.isArray(result.top3) ? result.top3 : [],
  };
}

function mapFavorites(items = []) {
  return items.map((item) => toFavoriteStackItem(item));
}

function mapHistory(items = []) {
  return items.map((item) => toHistoryStackItem(item));
}

async function loadBackendStatus() {
  try {
    const data = await checkHealth();
    backendStatus.value = `后端在线 · ${data.data?.default_model_name || "efficientnet_b0"}`;
    backendKind.value = "ok";
  } catch {
    backendStatus.value = "后端离线";
    backendKind.value = "warn";
  }
}

async function loadCatalog(query = "") {
  if (!query.trim()) {
    catalog.value = [];
    return;
  }

  loadingCatalog.value = true;
  try {
    const data = await fetchPlants(query);
    catalog.value = data.items || [];
  } catch {
    catalog.value = [];
  } finally {
    loadingCatalog.value = false;
  }
}

async function loadCatalogImages() {
  try {
    const response = await fetch("/plants/credits.json");
    if (!response.ok) return;
    const items = await response.json();
    catalogImages.value = Object.fromEntries(
      items
        .filter((item) => item?.class_id !== undefined && item?.image_url)
        .map((item) => [item.class_id, item.image_url])
    );
  } catch {
    catalogImages.value = {};
  }
}

async function loadPlantNames() {
  try {
    const data = await fetchPlants("");
    plantNames.value = Object.fromEntries(
      (data.items || []).map((item) => [item.class_id, item.display_name || item.name_cn || item.name_en])
    );
  } catch {
    plantNames.value = {};
  }
}

async function loadRemoteLists() {
  if (!canUseCloudRecords.value) {
    favorites.value = [];
    history.value = [];
    return;
  }

  try {
    const [favoritesData, historyData] = await Promise.all([
      fetchFavorites(),
      fetchHistory(50),
    ]);
    favorites.value = mapFavorites(favoritesData.items || []);
    history.value = mapHistory(historyData.items || []);
  } catch (error) {
    if (String(error.message || "").includes("401")) {
      clearSession();
      exitToAuthPage();
    }
  }
}

async function loadRagSessions() {
  if (!isLoggedIn.value) {
    ragSessions.value = [];
    return;
  }

  try {
    const data = await fetchRagSessions();
    ragSessions.value = data.items || [];
  } catch {
    ragSessions.value = [];
  }
}

function onFileChange(file) {
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    alert("请选择图片文件。");
    return;
  }

  currentFile.value = file;
  selectedResult.value = null;
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewUrl.value = URL.createObjectURL(file);
}

async function onPredict() {
  if (!currentFile.value) {
    alert("请先选择一张图片。");
    return;
  }

  loadingPredict.value = true;
  try {
    const data = normalizeResult(await predictFlower(currentFile.value));
    selectedResult.value = data;
    if (canUseCloudRecords.value) {
      await loadRemoteLists();
    }
  } catch (error) {
    alert(`识别失败：${error.message}`);
  } finally {
    loadingPredict.value = false;
  }
}

function onReset() {
  currentFile.value = null;
  selectedResult.value = null;
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = "";
  }
}

async function onFavorite() {
  if (!selectedResult.value) return;
  if (!isLoggedIn.value) {
    alert("登录后才能收藏识别结果。");
    return;
  }

  const plantId = selectedResult.value.plant?.id;
  if (!plantId) {
    alert("当前识别结果没有可收藏的花卉信息。");
    return;
  }

  try {
    await addFavorite(plantId);
    await loadRemoteLists();
  } catch (error) {
    alert(`收藏失败：${error.message}`);
  }
}

async function onRemoveFavorite(item) {
  if (!isLoggedIn.value || !item?.plantId) return;

  try {
    await removeFavorite(item.plantId);
    await loadRemoteLists();
  } catch (error) {
    alert(`删除收藏失败：${error.message}`);
  }
}

async function onRemoveHistory(item) {
  if (!isLoggedIn.value || !item?.id) return;

  try {
    await removeHistory(item.id);
    await loadRemoteLists();
  } catch (error) {
    alert(`删除历史失败：${error.message}`);
  }
}

async function onCopy() {
  if (!selectedResult.value) return;
  const text = [
    `花卉：${selectedResult.value.pred_name || "未知"}`,
    `类别：${selectedResult.value.pred_class ?? "-"}`,
    `置信度：${formatConfidence(selectedResult.value.confidence)}`,
  ].join("\n");
  await navigator.clipboard.writeText(text);
}

async function onSearchCatalog(query) {
  catalogQuery.value = query;
  await loadCatalog(query);
}

function blurNavItem(event) {
  event.currentTarget?.blur();
}

function startRagConversation(plant = null) {
  activeView.value = "rag";
  activeRagSessionId.value = null;
  ragCurrentPlant.value = plant || selectedPlant.value || null;
  ragSessionTitle.value = ragCurrentPlant.value ? `${ragCurrentPlant.value.display_name} 问答` : "花卉问答";
  ragMessages.value = [];
  ragError.value = "";
}

function openRagFromRecognition() {
  startRagConversation(selectedPlant.value);
}

function openRagFromCatalog(plant) {
  startRagConversation(plant);
}

function enterRagViewFromNav() {
  activeView.value = "rag";
  activeRagSessionId.value = null;
  ragCurrentPlant.value = selectedPlant.value || null;
  ragSessionTitle.value = ragCurrentPlant.value ? `${ragCurrentPlant.value.display_name} 问答` : "花卉问答";
  ragMessages.value = [];
  ragError.value = "";
}

async function onSelectRagSession(session) {
  if (!session?.id) return;
  activeView.value = "rag";
  activeRagSessionId.value = session.id;
  ragSessionTitle.value = session.title || ragSessionTitle.value;
  ragCurrentPlant.value = session.current_plant || null;
  ragError.value = "";

  try {
    const detail = await fetchRagSessionDetail(session.id);
    ragMessages.value = detail.messages || [];
    ragSessionTitle.value = detail.title || ragSessionTitle.value;
    ragCurrentPlant.value = detail.current_plant || ragCurrentPlant.value;
  } catch (error) {
    ragError.value = error.message;
  }
}

async function onDeleteRagSession(session) {
  if (!isLoggedIn.value || !session?.id) return;

  try {
    await deleteRagSession(session.id);
    if (activeRagSessionId.value === session.id) {
      activeRagSessionId.value = null;
      ragMessages.value = [];
      ragSessionTitle.value = ragCurrentPlant.value
        ? `${ragCurrentPlant.value.display_name} 问答`
        : "花卉问答";
    }
    await loadRagSessions();
  } catch (error) {
    alert(`删除会话失败：${error.message}`);
  }
}

async function onSendRagQuestion(question) {
  const normalizedQuestion = question.trim();
  if (!normalizedQuestion) return;

  ragLoading.value = true;
  ragError.value = "";

  const plantId = ragCurrentPlant.value?.id || selectedPlant.value?.id || null;
  const streamingAssistantId = `stream-assistant-${Date.now()}`;
  const optimisticUserMessage = {
    id: `stream-user-${Date.now()}`,
    session_id: activeRagSessionId.value || 0,
    role: "user",
    content: normalizedQuestion,
    retrieval_context: { provider: "streaming" },
    created_at: null,
  };
  const streamingAssistantMessage = {
    id: streamingAssistantId,
    session_id: activeRagSessionId.value || 0,
    role: "assistant",
    content: "",
    retrieval_context: { provider: "streaming" },
    created_at: null,
  };

  ragMessages.value = [...ragMessages.value, optimisticUserMessage, streamingAssistantMessage];

  const payload = {
    question: normalizedQuestion,
    session_id: isLoggedIn.value ? activeRagSessionId.value : null,
    plant_id: plantId,
    persist: isLoggedIn.value,
    recent_messages: isLoggedIn.value
      ? []
      : ragMessages.value.slice(-6).map((item) => ({
          role: item.role,
          content: item.content,
        })),
  };

  try {
    await sendRagChatStream(payload, {
      onStart(event) {
        ragSessionTitle.value = event.title || ragSessionTitle.value;
        activeRagSessionId.value = event.session_id || activeRagSessionId.value;
      },
      onDelta(content) {
        ragMessages.value = ragMessages.value.map((item) =>
          item.id === streamingAssistantId
            ? { ...item, content: `${item.content}${content}` }
            : item
        );
      },
      onDone(event) {
        ragSessionTitle.value = event.title || ragSessionTitle.value;
        activeRagSessionId.value = event.session_id || activeRagSessionId.value;
        if (!isLoggedIn.value) {
          ragMessages.value = event.recent_messages || ragMessages.value;
        }
      },
    });

    if (isLoggedIn.value && activeRagSessionId.value) {
      const detail = await fetchRagSessionDetail(activeRagSessionId.value);
      ragMessages.value = detail.messages || ragMessages.value;
      ragSessionTitle.value = detail.title || ragSessionTitle.value;
      await loadRagSessions();
    }
  } catch (error) {
    ragError.value = error.message;
    ragMessages.value = ragMessages.value.filter((item) => item.id !== streamingAssistantId);
  } finally {
    ragLoading.value = false;
  }
}

async function onLogin(payload) {
  authLoading.value = true;
  authError.value = "";
  try {
    const data = await login(payload);
    setSession(data.access_token, data.user);
    enterApp("user");
    await Promise.all([loadRemoteLists(), loadRagSessions()]);
  } catch (error) {
    authError.value = error.message;
  } finally {
    authLoading.value = false;
  }
}

async function onRegister(payload) {
  authLoading.value = true;
  authError.value = "";
  try {
    const data = await register(payload);
    setSession(data.access_token, data.user);
    enterApp("user");
    await Promise.all([loadRemoteLists(), loadRagSessions()]);
  } catch (error) {
    authError.value = error.message;
  } finally {
    authLoading.value = false;
  }
}

function onGuestEnter() {
  clearSession();
  enterApp("guest");
}

function onLogout() {
  clearSession();
  exitToAuthPage();
}

onMounted(async () => {
  clearSession();
  pageMode.value = "auth";
  await Promise.all([loadBackendStatus(), loadCatalogImages(), loadPlantNames()]);
});

onBeforeUnmount(() => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
});
</script>

<template>
  <div class="page-shell">
    <div class="ambient ambient-a"></div>
    <div class="ambient ambient-b"></div>

    <template v-if="pageMode === 'auth'">
      <section class="auth-landing auth-landing-center">
        <div class="auth-landing-header">
          <p class="auth-brand">花卉识别与科普系统</p>
          <p class="auth-brand-sub">识别 · 科普 · 收藏 · 历史 · 问答</p>
          <div class="status-row auth-status-row">
            <span class="status-pill" :class="backendKind">{{ backendStatus }}</span>
            <span class="status-pill muted">默认模型：EfficientNet-B0</span>
          </div>
        </div>

        <div class="auth-landing-panel">
          <AuthPanel
            :user="null"
            :loading="authLoading"
            :error="authError"
            @login="onLogin"
            @register="onRegister"
            @guest="onGuestEnter"
          />
        </div>
      </section>
    </template>

    <template v-else>
      <div class="workspace">
        <aside class="nav-rail">
          <div class="nav-peek">
            <span>菜单</span>
          </div>
          <div class="nav-top">
            <div>
              <div class="nav-brand">花卉平台</div>
              <div class="nav-sub">识别 · 科普 · 记录 · 问答</div>
            </div>
          </div>

          <div class="nav-group">
            <button class="nav-item" :class="{ active: activeView === 'recognition' }" type="button" @click="activeView = 'recognition'; blurNavItem($event)">
              <span>识别页</span>
            </button>
            <button class="nav-item" :class="{ active: activeView === 'rag' }" type="button" @click="enterRagViewFromNav(); blurNavItem($event)">
              <span>问答页</span>
            </button>
            <button class="nav-item" :class="{ active: activeView === 'catalog' }" type="button" @click="activeView = 'catalog'; blurNavItem($event)">
              <span>花卉科普库</span>
            </button>
            <button class="nav-item" :class="{ active: activeView === 'records' }" type="button" @click="activeView = 'records'; blurNavItem($event)">
              <span>平台记录</span>
            </button>
          </div>

          <div class="nav-panel" v-if="activeView === 'rag'">
            <div class="nav-panel-head">
              <div>
                <p class="section-label">问答会话</p>
                <h3>会话列表</h3>
              </div>
              <button class="mini-btn" type="button" @click="startRagConversation(ragFocusPlant)">新会话</button>
            </div>

            <div v-if="isLoggedIn" class="session-list">
              <article
                v-for="session in ragSessions"
                :key="session.id"
                class="session-item"
                :class="{ active: activeRagSessionId === session.id }"
              >
                <button class="session-main" type="button" @click="onSelectRagSession(session)">
                  <span class="session-title">{{ session.title }}</span>
                  <span class="session-meta">{{ session.current_plant?.display_name || '通用会话' }}</span>
                </button>
                <button
                  class="session-delete"
                  type="button"
                  title="删除会话"
                  @click.stop="onDeleteRagSession(session)"
                >
                  删除
                </button>
              </article>
              <div v-if="!ragSessions.length" class="session-empty">暂无历史会话</div>
            </div>
            <div v-else class="session-empty">游客模式仅保留当前会话</div>
          </div>

          <div class="nav-footer">
            <template v-if="isLoggedIn">
              <div class="nav-user">{{ currentUser?.username || 'user' }}</div>
              <button class="ghost-btn nav-logout" type="button" @click="onLogout">退出登录</button>
            </template>
            <template v-else>
              <div class="nav-user">游客模式</div>
              <div class="nav-note">关闭页面后会话失效</div>
            </template>
          </div>
        </aside>

        <div class="workspace-body">
          <header class="hero hero-slim">
            <div class="hero-copy">
              <p class="eyebrow">花卉识别平台</p>
              <h1>花卉识别与科普系统</h1>
              <p class="hero-text">
                上传图片即可进行识别；登录后可保存收藏、历史，并在问答页继续围绕当前花卉追问。
                游客模式可以正常识别和问答，但不会保存到数据库。
              </p>
            </div>

            <div class="hero-actions">
              <button v-if="selectedPlant" class="secondary-btn" type="button" @click="openRagFromRecognition">去问答</button>
              <button class="ghost-btn" type="button" @click="onLogout">退出</button>
            </div>
          </header>

          <main v-if="activeView === 'recognition'" class="layout recognition-layout">
            <UploadPanel
              :preview-url="previewUrl"
              :preview-file-name="previewFileName"
              :loading-catalog="loadingCatalog"
              @file-change="onFileChange"
              @predict="onPredict"
              @reset="onReset"
              @refresh-catalog="onSearchCatalog(catalogQuery)"
            />

            <ResultCard
              :result="selectedResultWithChineseTop3"
              :loading="loadingPredict"
              :can-favorite="isLoggedIn"
              @favorite="onFavorite"
              @copy="onCopy"
              @ask="openRagFromRecognition"
            />
          </main>

          <main v-else-if="activeView === 'catalog'" class="single-page-layout catalog-page-layout">
            <CatalogPanel
              :items="catalogWithImages"
              :count="catalog.length"
              :query="catalogQuery"
              :loading="loadingCatalog"
              @search="onSearchCatalog"
              @refresh="loadCatalog"
              @ask="openRagFromCatalog"
            />
          </main>

          <main v-else-if="activeView === 'records'" class="single-page-layout records-page-layout">
            <HistorySidebar
              :history="history"
              :favorites="favorites"
              :logged-in="isLoggedIn"
              :user-name="currentUser?.username || ''"
              :guest-mode="pageMode === 'app' && !isLoggedIn"
              @remove-favorite="onRemoveFavorite"
              @remove-history="onRemoveHistory"
            />
          </main>

          <main v-else-if="activeView === 'rag'" class="rag-layout">
            <RagPanel
              :session-id="activeRagSessionId"
              :session-title="ragDisplayTitle"
              :current-plant="ragFocusPlant"
              :messages="ragMessages"
              :loading="ragLoading"
              :error="ragError"
              :logged-in="isLoggedIn"
              :guest-mode="!isLoggedIn"
              @send="onSendRagQuestion"
              @new-session="startRagConversation(ragFocusPlant)"
              @back="activeView = 'recognition'"
            />
          </main>
        </div>
      </div>
    </template>
  </div>
</template>
