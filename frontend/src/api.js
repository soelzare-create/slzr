// Thin API client for the DaranX backend.
const TOKEN_KEY = "daranx_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`/api${path}`, { method, headers, body: payload });
  if (!res.ok) {
    let detail = `خطا (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = data.detail;
    } catch (_) {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

function qs(params) {
  const clean = Object.fromEntries(
    Object.entries(params || {}).filter(([, v]) => v !== "" && v != null)
  );
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
}

export const api = {
  // auth
  login: (phone, password) =>
    request("/auth/login", { method: "POST", form: { username: phone, password } }),
  me: () => request("/auth/me"),

  // users
  listUsers: () => request("/users"),
  createUser: (user) => request("/users", { method: "POST", body: user }),

  // team directory (any authenticated user — for assignment dropdowns)
  listTeam: () => request("/team"),

  // parties (customers and/or suppliers — one table, filter by role)
  listParties: (params) => request(`/parties${qs(params)}`),
  createParty: (p) => request("/parties", { method: "POST", body: p }),
  updateParty: (id, p) => request(`/parties/${id}`, { method: "PATCH", body: p }),

  // activities (core)
  listActivities: (params) => request(`/activities${qs(params)}`),
  getActivity: (id) => request(`/activities/${id}`),
  createActivity: (a) => request("/activities", { method: "POST", body: a }),
  updateActivity: (id, a) => request(`/activities/${id}`, { method: "PATCH", body: a }),
  addStage: (id, s) => request(`/activities/${id}/stages`, { method: "POST", body: s }),
};
