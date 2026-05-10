const API_BASE = "http://127.0.0.1:8000/api";
const STORAGE_KEYS = {
  history: "flower_history",
  favorites: "flower_favorites",
};

const el = {
  backendStatus: document.getElementById("backendStatus"),
  imageInput: document.getElementById("imageInput"),
  dropZone: document.getElementById("dropZone"),
  previewImage: document.getElementById("previewImage"),
  previewBox: document.querySelector(".preview-box"),
  uploadInfo: document.getElementById("uploadInfo"),
  predictBtn: document.getElementById("predictBtn"),
  loadPlantsBtn: document.getElementById("loadPlantsBtn"),
  resetBtn: document.getElementById("resetBtn"),
  favoriteBtn: document.getElementById("favoriteBtn"),
  copyBtn: document.getElementById("copyBtn"),
  predName: document.getElementById("predName"),
  predClass: document.getElementById("predClass"),
  confidence: document.getElementById("confidence"),
  confidenceFill: document.getElementById("confidenceFill"),
  resultBadge: document.getElementById("resultBadge"),
  topkList: document.getElementById("topkList"),
  plantDetail: document.getElementById("plantDetail"),
  catalogGrid: document.getElementById("catalogGrid"),
  catalogCount: document.getElementById("catalogCount"),
  catalogSearch: document.getElementById("catalogSearch"),
  historyList: document.getElementById("historyList"),
  favoriteList: document.getElementById("favoriteList"),
};

let selectedFile = null;
let currentResult = null;
let catalogCache = [];

function readJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function writeJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function setStatus(text, kind = "") {
  el.backendStatus.textContent = text;
  el.backendStatus.className = `status-pill ${kind}`.trim();
}

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function fmtConfidence(value) {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "-";
}

function renderHistory() {
  const template = document.getElementById("stackItemTemplate");
  const history = readJson(STORAGE_KEYS.history);
  const favorites = readJson(STORAGE_KEYS.favorites);

  const renderStack = (list, container, emptyText) => {
    if (!list.length) {
      container.innerHTML = `<div class="empty-state">${emptyText}</div>`;
      return;
    }

    container.innerHTML = "";
    list.slice(0, 6).forEach((item) => {
      const node = template.content.cloneNode(true);
      node.querySelector(".stack-title").textContent = item.title;
      node.querySelector(".stack-subtitle").textContent = item.subtitle;
      container.appendChild(node);
    });
  };

  renderStack(history, el.historyList, "Recent recognized flowers will appear here.");
  renderStack(favorites, el.favoriteList, "Saved favorites will appear here.");
}

function addHistory(result) {
  const history = readJson(STORAGE_KEYS.history);
  history.unshift({
    title: result.pred_name,
    subtitle: `${fmtConfidence(result.confidence)} · Class ${result.pred_class}`,
  });
  writeJson(STORAGE_KEYS.history, history.slice(0, 10));
}

function addFavorite(result) {
  const favorites = readJson(STORAGE_KEYS.favorites);
  if (favorites.some((item) => item.title === result.pred_name)) return;
  favorites.unshift({
    title: result.pred_name,
    subtitle: `${fmtConfidence(result.confidence)} · Saved locally`,
  });
  writeJson(STORAGE_KEYS.favorites, favorites.slice(0, 10));
}

function renderTopk(top3) {
  if (!top3 || !top3.length) {
    el.topkList.innerHTML = '<div class="placeholder">Candidate results will appear here.</div>';
    return;
  }

  el.topkList.innerHTML = top3
    .map(
      (item, index) => `
        <div class="topk-item">
          <div class="topk-main">
            <div class="topk-name">${index + 1}. ${esc(item.class_name)}</div>
            <div class="topk-meta">Class ID ${item.class_id}</div>
          </div>
          <div class="topk-score">${fmtConfidence(item.confidence)}</div>
        </div>
      `
    )
    .join("");
}

function renderPlant(plant) {
  if (!plant) {
    el.plantDetail.innerHTML =
      '<div class="placeholder">After recognition, this area will show the flower profile, flower language, and care tips.</div>';
    return;
  }

  const tips = (plant.care_tips || [])
    .map((tip) => `<li>${esc(tip)}</li>`)
    .join("");
  const tags = (plant.tags || [])
    .map((tag) => `<span class="tag">${esc(tag)}</span>`)
    .join("");

  el.plantDetail.innerHTML = `
    <div class="plant-title">${esc(plant.display_name)}</div>
    <div class="plant-section"><strong>English name:</strong> ${esc(plant.name_en)}</div>
    <div class="plant-section"><strong>Description:</strong> ${esc(plant.description)}</div>
    <div class="plant-section"><strong>Flower language:</strong> ${esc(plant.flower_language)}</div>
    <div class="plant-section"><strong>Season:</strong> ${esc(plant.season)}</div>
    <div class="plant-section">
      <strong>Care tips:</strong>
      <ul>${tips}</ul>
    </div>
    <div class="plant-section tag-row">${tags}</div>
  `;
}

function renderCatalog(list) {
  el.catalogCount.textContent = `${list.length} items`;
  if (!list.length) {
    el.catalogGrid.innerHTML = '<div class="catalog-empty">No matching plants found.</div>';
    return;
  }

  const template = document.getElementById("catalogCardTemplate");
  el.catalogGrid.innerHTML = "";
  list.forEach((item) => {
    const node = template.content.cloneNode(true);
    node.querySelector(".catalog-name").textContent = item.display_name;
    node.querySelector(".catalog-en").textContent = item.name_en;
    node.querySelector(".catalog-id").textContent = `#${item.class_id}`;
    node.querySelector(".catalog-desc").textContent = item.description;
    const tagRow = node.querySelector(".tag-row");
    (item.tags || []).forEach((tag) => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = tag;
      tagRow.appendChild(span);
    });
    el.catalogGrid.appendChild(node);
  });
}

async function checkBackend() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    setStatus(`Backend online · ${data.data?.default_model_name || "efficientnet_b0"}`, "ok");
  } catch {
    setStatus("Backend offline", "warn");
  }
}

async function loadCatalog(query = "") {
  const url = new URL(`${API_BASE}/plants`);
  if (query.trim()) url.searchParams.set("query", query.trim());

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    catalogCache = data.items || [];
    renderCatalog(catalogCache);
  } catch {
    el.catalogGrid.innerHTML = '<div class="catalog-empty">Catalog load failed. Make sure the backend is running.</div>';
  }
}

function showResult(result) {
  currentResult = result;
  el.predName.textContent = result.pred_name || "-";
  el.predClass.textContent = result.pred_class ?? "-";
  el.confidence.textContent = fmtConfidence(result.confidence);
  el.confidenceFill.style.width = `${Math.min(Math.max(result.confidence || 0, 0), 100)}%`;
  el.resultBadge.textContent = "Recognition complete";
  el.favoriteBtn.disabled = false;
  el.copyBtn.disabled = false;
  renderTopk(result.top3 || []);
  renderPlant(result.plant || null);
  addHistory(result);
  renderHistory();
}

function clearResult() {
  selectedFile = null;
  currentResult = null;
  el.imageInput.value = "";
  el.previewImage.removeAttribute("src");
  el.previewBox.classList.remove("has-image");
  el.uploadInfo.textContent = "No image selected.";
  el.predName.textContent = "Ready";
  el.predClass.textContent = "-";
  el.confidence.textContent = "-";
  el.confidenceFill.style.width = "0%";
  el.resultBadge.textContent = "Waiting";
  el.favoriteBtn.disabled = true;
  el.copyBtn.disabled = true;
  el.topkList.innerHTML = '<div class="placeholder">Candidate results will appear here.</div>';
  el.plantDetail.innerHTML =
    '<div class="placeholder">After recognition, this area will show the flower profile, flower language, and care tips.</div>';
  setStatus("Backend checking...");
}

function handleFile(file) {
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    alert("Please choose an image file.");
    return;
  }

  selectedFile = file;
  el.uploadInfo.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
  el.previewImage.src = URL.createObjectURL(file);
  el.previewBox.classList.add("has-image");
}

async function predict() {
  if (!selectedFile) {
    alert("Please select an image first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  el.predictBtn.disabled = true;
  el.predictBtn.textContent = "Recognizing...";
  el.resultBadge.textContent = "Predicting";

  try {
    const response = await fetch(`${API_BASE}/recognition/predict?topk=3`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    showResult(data);
  } catch (error) {
    el.resultBadge.textContent = "Recognition failed";
    alert(`Recognition failed: ${error.message}`);
  } finally {
    el.predictBtn.disabled = false;
    el.predictBtn.textContent = "Start Recognition";
  }
}

async function copyResult() {
  if (!currentResult) return;
  const text = [
    `Flower: ${currentResult.pred_name}`,
    `Class: ${currentResult.pred_class}`,
    `Confidence: ${fmtConfidence(currentResult.confidence)}`,
  ].join("\n");
  await navigator.clipboard.writeText(text);
  el.copyBtn.textContent = "Copied";
  setTimeout(() => {
    el.copyBtn.textContent = "Copy Result";
  }, 1200);
}

function bindEvents() {
  el.imageInput.addEventListener("change", (event) => {
    handleFile(event.target.files?.[0]);
  });

  el.dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    el.dropZone.classList.add("dragover");
  });

  el.dropZone.addEventListener("dragleave", () => {
    el.dropZone.classList.remove("dragover");
  });

  el.dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    el.dropZone.classList.remove("dragover");
    handleFile(event.dataTransfer.files?.[0]);
  });

  el.predictBtn.addEventListener("click", predict);
  el.loadPlantsBtn.addEventListener("click", () => loadCatalog(el.catalogSearch.value));
  el.resetBtn.addEventListener("click", clearResult);
  el.favoriteBtn.addEventListener("click", () => {
    if (!currentResult) return;
    addFavorite(currentResult);
    renderHistory();
  });
  el.copyBtn.addEventListener("click", copyResult);

  el.catalogSearch.addEventListener("input", (event) => {
    const keyword = event.target.value.trim().toLowerCase();
    if (!keyword) {
      renderCatalog(catalogCache);
      return;
    }
    const filtered = catalogCache.filter((item) => {
      const haystack = `${item.display_name} ${item.name_en} ${item.description} ${(item.tags || []).join(" ")}`.toLowerCase();
      return haystack.includes(keyword);
    });
    renderCatalog(filtered);
  });
}

async function init() {
  bindEvents();
  renderHistory();
  await checkBackend();
  await loadCatalog();
}

init();
