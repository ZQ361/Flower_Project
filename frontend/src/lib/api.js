const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

function getToken() {
  return window.sessionStorage.getItem("flower_access_token") || "";
}

function buildHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: buildHeaders(options.headers || {}),
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || `HTTP ${response.status}`);
  }

  return data;
}

export async function checkHealth() {
  return request("/health");
}

export async function fetchPlants(query = "") {
  const url = new URL(`${API_BASE}/plants`, window.location.origin);
  if (query.trim()) {
    url.searchParams.set("query", query.trim());
  }
  const response = await fetch(url, { headers: buildHeaders() });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

export async function predictFlower(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/recognition/predict?topk=3`, {
    method: "POST",
    body: formData,
    headers: buildHeaders(),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return data;
}

export async function register(payload) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function login(payload) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchCurrentUser() {
  return request("/auth/me");
}

export async function fetchFavorites() {
  return request("/favorites");
}

export async function addFavorite(plantId, note = "") {
  return request(`/favorites/${plantId}`, {
    method: "POST",
    headers: note ? { "Content-Type": "application/json" } : undefined,
    body: note ? JSON.stringify({ note }) : undefined,
  });
}

export async function removeFavorite(plantId) {
  return request(`/favorites/${plantId}`, { method: "DELETE" });
}

export async function fetchHistory(limit = 50) {
  return request(`/history?limit=${limit}`);
}

export async function removeHistory(historyId) {
  return request(`/history/${historyId}`, { method: "DELETE" });
}

export async function fetchRagSessions() {
  return request("/rag/sessions");
}

export async function fetchRagSessionDetail(sessionId) {
  return request(`/rag/sessions/${sessionId}`);
}

export async function deleteRagSession(sessionId) {
  return request(`/rag/sessions/${sessionId}`, { method: "DELETE" });
}

export async function sendRagChat(payload) {
  return request("/rag/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function sendRagChatStream(payload, handlers = {}) {
  const response = await fetch(`${API_BASE}/rag/chat/stream`, {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || data?.message || `HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const text = line.trim();
      if (!text) continue;
      const event = JSON.parse(text);
      if (event.type === "start") handlers.onStart?.(event);
      if (event.type === "delta") handlers.onDelta?.(event.content || "", event);
      if (event.type === "done") handlers.onDone?.(event);
      if (event.type === "error") throw new Error(event.message || "流式问答失败");
    }
  }

  const tail = buffer.trim();
  if (tail) {
    const event = JSON.parse(tail);
    if (event.type === "start") handlers.onStart?.(event);
    if (event.type === "delta") handlers.onDelta?.(event.content || "", event);
    if (event.type === "done") handlers.onDone?.(event);
    if (event.type === "error") throw new Error(event.message || "流式问答失败");
  }
}
