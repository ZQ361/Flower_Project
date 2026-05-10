<script setup>
defineProps({
  history: {
    type: Array,
    default: () => [],
  },
  favorites: {
    type: Array,
    default: () => [],
  },
  loggedIn: {
    type: Boolean,
    default: false,
  },
  userName: {
    type: String,
    default: "",
  },
  guestMode: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["remove-history", "remove-favorite"]);
</script>

<template>
  <section class="card side-card">
    <div class="card-head">
      <div>
        <p class="section-label">平台记录</p>
        <h2>最近识别 / 收藏</h2>
      </div>
    </div>

    <p v-if="guestMode" class="history-note">当前是游客模式，识别记录不会保存到数据库。</p>
    <p v-else-if="loggedIn" class="history-note">
      当前账号：{{ userName || "已登录用户" }}，收藏和历史已同步到 SQLite。
    </p>
    <p v-else class="history-note">登录后可以查看收藏和历史记录。</p>

    <div class="mini-columns">
      <div class="mini-block">
        <h3>最近识别</h3>
        <div id="historyList" class="stack-list">
          <div v-if="history.length">
            <article v-for="item in history.slice(0, 6)" :key="item.id ?? `${item.title}-${item.subtitle}`" class="stack-item">
              <div class="stack-row">
                <div class="stack-copy">
                  <div class="stack-title">{{ item.title }}</div>
                  <div class="stack-subtitle">{{ item.subtitle }}</div>
                </div>
                <button
                  v-if="loggedIn && item.id"
                  class="tiny-icon-btn"
                  type="button"
                  title="删除历史"
                  @click="emit('remove-history', item)"
                >
                  删除
                </button>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">最近识别记录会显示在这里。</div>
        </div>
      </div>

      <div class="mini-block">
        <h3>我的收藏</h3>
        <div id="favoriteList" class="stack-list">
          <div v-if="favorites.length">
            <article v-for="item in favorites.slice(0, 6)" :key="item.id ?? `${item.title}-${item.subtitle}`" class="stack-item">
              <div class="stack-row">
                <div class="stack-copy">
                  <div class="stack-title">{{ item.title }}</div>
                  <div class="stack-subtitle">{{ item.subtitle }}</div>
                </div>
                <button
                  v-if="loggedIn && item.plantId"
                  class="tiny-icon-btn"
                  type="button"
                  title="删除收藏"
                  @click="emit('remove-favorite', item)"
                >
                  删除
                </button>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">收藏后会显示在这里。</div>
        </div>
      </div>
    </div>
  </section>
</template>
