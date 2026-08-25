// Tiny fetch wrapper with JWT + friendly Persian error surfacing.
const TOKEN_KEY = "daranx_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    setToken(null);
    if (!path.startsWith("/auth/login")) window.location.hash = "#/login";
  }

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    const message = extractError(data) || `خطا (${res.status})`;
    throw new Error(message);
  }
  return data;
}

function extractError(data) {
  if (!data) return null;
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  // DRF field errors → first message
  const first = Object.values(data)[0];
  if (Array.isArray(first)) return first[0];
  if (typeof first === "string") return first;
  return null;
}

export const api = {
  get: (p) => request("GET", p),
  post: (p, b) => request("POST", p, b),
  put: (p, b) => request("PUT", p, b),
  patch: (p, b) => request("PATCH", p, b),
  del: (p) => request("DELETE", p),
};

// List endpoints are paginated; unwrap results transparently.
export function rows(data) {
  return Array.isArray(data) ? data : data?.results ?? [];
}

export function toman(n) {
  const v = Number(n || 0);
  return v.toLocaleString("fa-IR") + " تومان";
}
