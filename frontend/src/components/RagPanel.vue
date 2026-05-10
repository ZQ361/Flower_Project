<script setup>
import { computed, ref } from "vue";
import { formatDateTime } from "../lib/storage";

const props = defineProps({
  sessionId: {
    type: [Number, String],
    default: null,
  },
  sessionTitle: {
    type: String,
    default: "花卉问答",
  },
  currentPlant: {
    type: Object,
    default: null,
  },
  messages: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: "",
  },
  loggedIn: {
    type: Boolean,
    default: false,
  },
  guestMode: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["send", "new-session", "back"]);
const draft = ref("");

const hasPlant = computed(() => Boolean(props.currentPlant));
const plantCareTips = computed(() => (Array.isArray(props.currentPlant?.care_tips) ? props.currentPlant.care_tips : []));
const plantTags = computed(() => (Array.isArray(props.currentPlant?.tags) ? props.currentPlant.tags : []));

function submitQuestion() {
  const question = draft.value.trim();
  if (!question) return;
  emit("send", question);
  draft.value = "";
}

function roleLabel(role) {
  return role === "assistant" ? "花卉助手" : "我";
}

function providerLabel(item) {
  const provider = item?.retrieval_context?.provider;
  if (provider === "bailian") return "百炼生成";
  if (provider === "local-fallback") return "本地兜底";
  if (provider === "client-memory") return "游客记忆";
  if (provider === "streaming") return "生成中";
  return "问答记录";
}
</script>

<template>
  <section class="card rag-card">
    <div class="card-head rag-card-head">
      <div>
        <p class="section-label">智能问答</p>
        <h2>{{ sessionTitle }}</h2>
      </div>
      <div class="rag-actions">
        <button class="ghost-btn" type="button" @click="$emit('back')">返回识别</button>
        <button class="primary-btn" type="button" @click="$emit('new-session')">新会话</button>
      </div>
    </div>

    <div v-if="hasPlant" class="rag-context card-soft">
      <div class="rag-context-top">
        <div>
          <p class="section-label">当前花卉</p>
          <h3>{{ currentPlant.display_name }}</h3>
        </div>
        <span class="chip">{{ currentPlant.name_en }}</span>
      </div>
      <p class="rag-context-desc">{{ currentPlant.description }}</p>
      <div class="rag-context-grid">
        <div class="rag-context-item"><strong>花语</strong><span>{{ currentPlant.flower_language }}</span></div>
        <div class="rag-context-item"><strong>花期</strong><span>{{ currentPlant.season }}</span></div>
        <div class="rag-context-item"><strong>生长环境</strong><span>{{ currentPlant.habitat || '暂无' }}</span></div>
      </div>
      <div v-if="plantCareTips.length" class="tag-row">
        <span v-for="tip in plantCareTips" :key="tip" class="tag">{{ tip }}</span>
      </div>
      <div v-if="plantTags.length" class="tag-row">
        <span v-for="tag in plantTags" :key="tag" class="tag subtle">{{ tag }}</span>
      </div>
    </div>

    <div v-else class="rag-context card-soft empty">
      你可以先从识别页选择一张花图，再带着当前花卉继续提问。
    </div>

    <div class="rag-meta-row">
      <span class="status-pill muted">{{ loggedIn ? '登录会话已保存' : '游客短期记忆' }}</span>
      <span v-if="sessionId" class="status-pill muted">会话 ID：{{ sessionId }}</span>
    </div>

    <p v-if="error" class="rag-error">{{ error }}</p>

    <div class="rag-chat-list">
      <div v-if="messages.length">
        <article
          v-for="(item, index) in messages"
          :key="`${item.id || index}-${item.role}`"
          class="rag-bubble"
          :class="item.role"
        >
          <div class="rag-bubble-head">
            <strong>{{ roleLabel(item.role) }}</strong>
            <span>{{ providerLabel(item) }}</span>
            <span v-if="item.created_at">{{ formatDateTime(item.created_at) }}</span>
          </div>
          <div class="rag-bubble-body">{{ item.content }}</div>
        </article>
      </div>
      <div v-else class="rag-empty">
        输入一个问题，系统会基于当前花卉资料和最近对话给出回答。
      </div>
    </div>

    <form class="rag-input-panel" @submit.prevent="submitQuestion">
      <label class="field-group rag-field">
        <span>问题</span>
        <textarea
          v-model="draft"
          rows="4"
          :disabled="loading"
          placeholder="例如：这朵花适合放阳台吗？"
        ></textarea>
      </label>
      <div class="rag-input-footer">
        <p class="rag-hint">
          {{ guestMode ? '游客模式仅保留当前会话上下文，关闭页面后失效。' : '登录后会保存会话，后续可以继续追问。' }}
        </p>
        <div class="rag-input-actions">
          <button class="ghost-btn" type="button" :disabled="loading" @click="$emit('new-session')">重置会话</button>
          <button class="primary-btn" type="submit" :disabled="loading || !draft.trim()">
            {{ loading ? '生成中...' : '发送问题' }}
          </button>
        </div>
      </div>
    </form>
  </section>
</template>
