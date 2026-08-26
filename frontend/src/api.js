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

// --- Jalali (Shamsi) date display -----------------------------------------
// Uses jalaali-js (deterministic) rather than Intl's Persian calendar, which
// is unreliable in some engines. Keeps display consistent with the date picker.
import { toJalaali } from "jalaali-js";

const J_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
  "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
const faDigits = (n) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);

/** Format an ISO date/datetime string as a Persian (Jalali) date. */
export function jalali(value, withTime = false) {
  if (!value) return "—";
  let gy, gm, gd, time = "";
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    [gy, gm, gd] = value.split("-").map(Number); // date-only, no TZ shift
  } else {
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    gy = d.getFullYear(); gm = d.getMonth() + 1; gd = d.getDate();
    if (withTime) time = ` ${faDigits(String(d.getHours()).padStart(2, "0"))}:${faDigits(String(d.getMinutes()).padStart(2, "0"))}`;
  }
  const j = toJalaali(gy, gm, gd);
  return `${faDigits(j.jd)} ${J_MONTHS[j.jm - 1]} ${faDigits(j.jy)}${time}`;
}
