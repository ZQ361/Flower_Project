<script setup>
import { computed } from "vue";
import { formatConfidence } from "../lib/storage";

const props = defineProps({
  result: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  canFavorite: {
    type: Boolean,
    default: true,
  },
});

defineEmits(["favorite", "copy", "ask"]);

const plantInfo = computed(() => props.result?.plant || null);
const resultTitle = computed(() => plantInfo.value?.display_name || props.result?.pred_name || "等待识别");
const resultBadge = computed(() => {
  if (props.loading) return "识别中";
  if (props.result) return "识别完成";
  return "等待识别";
});
const confidenceWidth = computed(() => {
  const confidence = props.result?.confidence || 0;
  return `${Math.min(Math.max(confidence, 0), 100)}%`;
});
const top3List = computed(() => (Array.isArray(props.result?.top3) ? props.result.top3 : []));
const careTips = computed(() => (Array.isArray(plantInfo.value?.care_tips) ? plantInfo.value.care_tips : []));
const tags = computed(() => (Array.isArray(plantInfo.value?.tags) ? plantInfo.value.tags : []));
</script>

<template>
  <section class="card result-card">
    <div class="card-head">
      <div>
        <p class="section-label">识别结果</p>
        <h2>模型输出</h2>
      </div>
      <div id="resultBadge" class="result-badge">
        {{ resultBadge }}
      </div>
    </div>

    <div class="result-main">
      <div class="result-core">
        <div id="predName" class="result-name">{{ resultTitle }}</div>
        <div class="result-meta">
          <span>类别 ID：<strong id="predClass">{{ result?.pred_class ?? "-" }}</strong></span>
          <span>置信度：<strong id="confidence">{{ formatConfidence(result?.confidence) }}</strong></span>
        </div>
        <div class="confidence-bar">
          <div id="confidenceFill" class="confidence-fill" :style="{ width: confidenceWidth }"></div>
        </div>
      </div>

      <div class="action-row">
        <button class="secondary-btn" type="button" :disabled="!result || !canFavorite" @click="$emit('favorite')">
          {{ canFavorite ? "收藏本次识别" : "登录后收藏" }}
        </button>
        <button class="secondary-btn" type="button" :disabled="!result" @click="$emit('ask')">
          去问答
        </button>
        <button class="ghost-btn" type="button" :disabled="!result" @click="$emit('copy')">
          复制结果
        </button>
      </div>
    </div>

    <div class="subgrid">
      <div class="subcard">
        <h3>Top-3 候选</h3>
        <div id="topkList" class="topk-list">
          <template v-if="top3List.length">
            <div v-for="(item, index) in top3List" :key="`${item.class_id}-${index}`" class="topk-item">
              <div class="topk-main">
                <div class="topk-name">{{ index + 1 }}. {{ item.display_name || item.class_name || item.name_en || "未知类别" }}</div>
                <div class="topk-meta">类别 ID {{ item.class_id }}</div>
              </div>
              <div class="topk-score">{{ formatConfidence(item.confidence) }}</div>
            </div>
          </template>
          <div v-else class="placeholder">识别后这里会显示候选结果。</div>
        </div>
      </div>

      <div class="subcard">
        <h3>科普信息</h3>
        <div id="plantDetail" class="plant-detail">
          <template v-if="plantInfo">
            <div class="plant-title">{{ plantInfo.display_name }}</div>
            <div class="plant-section"><strong>英文名：</strong>{{ plantInfo.name_en }}</div>
            <div class="plant-section"><strong>简介：</strong>{{ plantInfo.description }}</div>
            <div class="plant-section"><strong>花语：</strong>{{ plantInfo.flower_language }}</div>
            <div class="plant-section"><strong>花期：</strong>{{ plantInfo.season }}</div>
            <div class="plant-section">
              <strong>养护建议：</strong>
              <ul>
                <li v-for="(tip, index) in careTips" :key="index">{{ tip }}</li>
              </ul>
            </div>
            <div class="plant-section tag-row">
              <span v-for="tag in tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </template>
          <div v-else class="placeholder">
            识别命中后，这里会展示对应花卉的简介、花语和养护建议。
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
