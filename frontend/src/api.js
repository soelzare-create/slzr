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
  // party contacts (افراد رابط — سمت/نام/شماره per person)
  listPartyContacts: (id) => request(`/parties/${id}/contacts`),
  addPartyContact: (id, c) =>
    request(`/parties/${id}/contacts`, { method: "POST", body: c }),
  deletePartyContact: (id, contactId) =>
    request(`/parties/${id}/contacts/${contactId}`, { method: "DELETE" }),

  // inventory (warehouse)
  listProductModels: (params) => request(`/product-models${qs(params)}`),
  getProductModel: (id) => request(`/product-models/${id}`),
  createProductModel: (m) => request("/product-models", { method: "POST", body: m }),
  updateProductModel: (id, m) =>
    request(`/product-models/${id}`, { method: "PATCH", body: m }),
  listStockItems: (params) => request(`/stock-items${qs(params)}`),
  createStockItem: (s) => request("/stock-items", { method: "POST", body: s }),
  updateStockItem: (id, s) => request(`/stock-items/${id}`, { method: "PATCH", body: s }),

  // activities (core)
  listActivities: (params) => request(`/activities${qs(params)}`),
  getActivity: (id) => request(`/activities/${id}`),
  createActivity: (a) => request("/activities", { method: "POST", body: a }),
  updateActivity: (id, a) => request(`/activities/${id}`, { method: "PATCH", body: a }),
  addStage: (id, s) => request(`/activities/${id}/stages`, { method: "POST", body: s }),

  // invoices (sales: proforma / final) — each invoice carries its own line items
  listInvoices: (params) => request(`/invoices${qs(params)}`),
  getInvoice: (id) => request(`/invoices/${id}`),
  createInvoice: (inv) => request("/invoices", { method: "POST", body: inv }),
  updateInvoice: (id, inv) => request(`/invoices/${id}`, { method: "PATCH", body: inv }),
  deleteInvoice: (id) => request(`/invoices/${id}`, { method: "DELETE" }),

  // purchases (buying: record a purchase from a supplier)
  listPurchases: (params) => request(`/purchases${qs(params)}`),
  createPurchase: (p) => request("/purchases", { method: "POST", body: p }),
  updatePurchase: (id, p) => request(`/purchases/${id}`, { method: "PATCH", body: p }),

  // accounting (ledger, per-party balances, summary, payments/receipts)
  accountingSummary: () => request("/accounting/summary"),
  accountingBalances: () => request("/accounting/balances"),
  accountingDocuments: (params) => request(`/accounting/documents${qs(params)}`),
  listPayments: (params) => request(`/accounting/payments${qs(params)}`),
  createPayment: (p) => request("/accounting/payments", { method: "POST", body: p }),
  listCashAccounts: () => request("/accounting/accounts"),
  createCashAccount: (a) => request("/accounting/accounts", { method: "POST", body: a }),
  expenseByCategory: () => request("/accounting/expense-by-category"),
  listCheques: (params) => request(`/accounting/cheques${qs(params)}`),
  createCheque: (c) => request("/accounting/cheques", { method: "POST", body: c }),
  clearCheque: (id, body) =>
    request(`/accounting/cheques/${id}/clear`, { method: "POST", body: body || {} }),
  bounceCheque: (id) =>
    request(`/accounting/cheques/${id}/bounce`, { method: "POST" }),

  // tasks (internal referrals — ارجاعات)
  listTasks: (params) => request(`/tasks${qs(params)}`),
  createTask: (t) => request("/tasks", { method: "POST", body: t }),
  updateTask: (id, t) => request(`/tasks/${id}`, { method: "PATCH", body: t }),

  // reports (management overview)
  reportsOverview: () => request("/reports/overview"),
};
