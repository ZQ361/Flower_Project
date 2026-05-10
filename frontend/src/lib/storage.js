const AUTH_TOKEN_KEY = "flower_access_token";
const AUTH_USER_KEY = "flower_user";

function getAuthStore() {
  return window.sessionStorage;
}

export function getAuthToken() {
  return getAuthStore().getItem(AUTH_TOKEN_KEY) || "";
}

export function getAuthUser() {
  try {
    const raw = getAuthStore().getItem(AUTH_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setAuthSession(token, user) {
  const store = getAuthStore();
  store.setItem(AUTH_TOKEN_KEY, token);
  store.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  const store = getAuthStore();
  store.removeItem(AUTH_TOKEN_KEY);
  store.removeItem(AUTH_USER_KEY);

  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
}

export function formatConfidence(value) {
  return typeof value === "number" ? `${value.toFixed(2)}%` : "-";
}

export function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Shanghai",
  });
}

export function toHistoryStackItem(item) {
  const title = item?.plant?.display_name || item?.pred_name || "Unknown";
  const parts = [formatConfidence(item?.confidence), item?.source || "历史记录", formatDateTime(item?.created_at)].filter(Boolean);

  return {
    id: item?.id ?? null,
    plantId: item?.plant?.id ?? null,
    title,
    subtitle: parts.join(" | "),
  };
}

export function toFavoriteStackItem(item) {
  const title = item?.plant?.display_name || item?.plant?.name_en || "Unknown";
  const parts = [item?.plant?.flower_language || "已收藏花卉", item?.note || null, formatDateTime(item?.created_at)].filter(Boolean);

  return {
    id: item?.id ?? null,
    plantId: item?.plant?.id ?? null,
    title,
    subtitle: parts.join(" | "),
  };
}
