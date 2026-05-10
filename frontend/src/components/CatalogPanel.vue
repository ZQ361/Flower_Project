<script setup>
import { computed } from "vue";
import { ref } from "vue";

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  count: {
    type: Number,
    default: 0,
  },
  query: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["search", "refresh", "ask"]);
const previewImage = ref(null);

const hasQuery = computed(() => Boolean(props.query.trim()));

function onInput(event) {
  emit("search", event.target.value);
}

function onImageError(event) {
  event.currentTarget.classList.add("hidden");
}

function openPreview(item) {
  if (!item.image_url) return;
  previewImage.value = item;
}

function closePreview() {
  previewImage.value = null;
}
</script>

<template>
  <section class="card catalog-card">
    <div class="card-head">
      <div>
        <p class="section-label">花卉科普库</p>
        <h2>可浏览条目</h2>
      </div>
      <span id="catalogCount" class="chip">{{ count }} 项</span>
    </div>

    <div class="catalog-search">
      <input
        id="catalogSearch"
        :value="query"
        type="text"
        placeholder="搜索花名，例如 rose / sunflower / lotus"
        @input="onInput"
      />
    </div>

    <div id="catalogGrid" class="catalog-grid">
      <div v-if="loading" class="catalog-empty">科普库加载中...</div>
      <div v-else-if="!hasQuery" class="catalog-empty">请输入关键词后再显示结果。</div>
      <template v-else-if="items.length">
        <article v-for="item in items" :key="item.class_id" class="catalog-item">
          <button
            class="catalog-thumb"
            type="button"
            :disabled="!item.image_url"
            :title="item.image_url ? `查看${item.display_name}完整图片` : ''"
            @click="openPreview(item)"
          >
            <img
              v-if="item.image_url"
              :src="item.image_url"
              :alt="item.display_name"
              loading="lazy"
              @error="onImageError"
            />
            <span v-else>{{ item.display_name?.slice(0, 1) || "花" }}</span>
          </button>

          <div class="catalog-copy">
            <div class="catalog-item-top">
              <div>
                <div class="catalog-name">{{ item.display_name }}</div>
                <div class="catalog-en">{{ item.name_en }}</div>
              </div>
              <span class="catalog-id">#{{ item.class_id }}</span>
            </div>
            <p class="catalog-desc">{{ item.description }}</p>
            <div class="tag-row">
              <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
            <div class="catalog-actions">
              <button class="mini-btn" type="button" @click="emit('ask', item)">围绕它问答</button>
            </div>
          </div>
        </article>
      </template>
      <div v-else class="catalog-empty">没有匹配到条目。</div>
    </div>

    <teleport to="body">
      <div v-if="previewImage" class="image-preview-backdrop" @click.self="closePreview">
        <figure class="image-preview-dialog">
          <button class="image-preview-close" type="button" aria-label="关闭图片预览" @click="closePreview">×</button>
          <img :src="previewImage.image_url" :alt="previewImage.display_name" />
          <figcaption>
            <strong>{{ previewImage.display_name }}</strong>
            <span>{{ previewImage.name_en }}</span>
          </figcaption>
        </figure>
      </div>
    </teleport>
  </section>
</template>
