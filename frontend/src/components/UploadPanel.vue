<script setup>
defineProps({
  previewUrl: {
    type: String,
    default: "",
  },
  previewFileName: {
    type: String,
    default: "未选择图片",
  },
  loadingCatalog: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["file-change", "predict", "reset", "refresh-catalog"]);

function handleSelect(event) {
  emit("file-change", event.target.files?.[0] || null);
}

function handleDrop(event) {
  event.preventDefault();
  event.currentTarget.classList.remove("dragover");
  emit("file-change", event.dataTransfer.files?.[0] || null);
}

function handleDragOver(event) {
  event.currentTarget.classList.add("dragover");
}

function handleDragLeave(event) {
  event.currentTarget.classList.remove("dragover");
}
</script>

<template>
  <section class="card upload-card">
    <div class="card-head">
      <div>
        <p class="section-label">识别入口</p>
        <h2>上传图片</h2>
      </div>
      <button class="ghost-btn" type="button" @click="$emit('reset')">重置</button>
    </div>

    <div
      id="dropZone"
      class="upload-zone"
      @dragover.prevent="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <input id="imageInput" type="file" accept="image/*" @change="handleSelect" />
      <div class="upload-icon">花</div>
      <p class="upload-title">把花卉图片拖到这里，或者点击选择文件</p>
      <p class="upload-hint">支持 JPG、PNG、WEBP 等常见格式</p>
    </div>

    <div class="preview-grid">
      <div class="preview-box" :class="{ 'has-image': !!previewUrl }">
        <img id="previewImage" :src="previewUrl" alt="图片预览" />
        <div id="previewEmpty" class="preview-empty">预览区域</div>
      </div>

      <div class="action-stack">
        <button class="primary-btn" type="button" @click="$emit('predict')">开始识别</button>
        <button class="secondary-btn" type="button" :disabled="loadingCatalog" @click="$emit('refresh-catalog')">
          {{ loadingCatalog ? "刷新中..." : "刷新科普库" }}
        </button>
        <p id="uploadInfo" class="mini-note">{{ previewFileName }}</p>
      </div>
    </div>
  </section>
</template>
