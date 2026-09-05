import { useEffect, useState } from "react";
import { api, rows } from "./api";

// Modal now lives in ui.jsx (icon header, close button). Re-export for pages.
export { Modal } from "./ui.jsx";

const PROFORMA_BADGE = {
  DRAFT: "gray", CONFIRMED: "blue", AWAITING_PURCHASE: "amber",
  READY: "green", INVOICED: "green", CANCELLED: "red", UNFULFILLABLE: "red",
};
const INVOICE_BADGE = { ISSUED: "green", CANCELLED: "red", RETURNED: "amber" };
const PURCHASE_BADGE = { DRAFT: "gray", REGISTERED: "green", CANCELLED: "red" };

export function StatusBadge({ status, display, kind = "proforma" }) {
  const map = kind === "invoice" ? INVOICE_BADGE : kind === "purchase" ? PURCHASE_BADGE : PROFORMA_BADGE;
  return <span className={`badge ${map[status] || "gray"}`}>{display || status}</span>;
}

// Hook: load a list endpoint with reload support.
export function useList(path) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function reload() {
    setLoading(true);
    api.get(path)
      .then((d) => setData(rows(d)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { reload(); }, [path]);
  return { data, loading, error, reload, setError };
}

// Options loader for a <select>.
export function useOptions(path) {
  const [opts, setOpts] = useState([]);
  useEffect(() => { api.get(path).then((d) => setOpts(rows(d))).catch(() => {}); }, [path]);
  return opts;
}

// Reloadable catalog of items (goods/services). Unlike useOptions it exposes a
// reload() so a freshly-created item shows up immediately in the picker.
export function useItems() {
  const [items, setItems] = useState([]);
  function reload() { api.get("/items").then((d) => setItems(rows(d))).catch(() => {}); }
  useEffect(() => { reload(); }, []);
  return { items, reload };
}

// Searchable item picker for invoice/proforma/purchase lines.
// Type to filter by name or SKU; pick a result to select it. If nothing matches
// the typed text, create it on the spot as a کالا (goods) or خدمت (service) —
// it is saved to the catalog and selected immediately.
export function ItemPicker({ items, value, onChange, reloadItems, allowCreate = true }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);

  const selected = items.find((i) => String(i.id) === String(value));
  const query = q.trim();
  const ql = query.toLowerCase();
  const matches = ql
    ? items.filter((i) =>
        i.name.toLowerCase().includes(ql) || (i.sku || "").toLowerCase().includes(ql))
    : items;
  const exact = items.some((i) => i.name.trim().toLowerCase() === ql);

  function choose(id) { onChange(String(id)); setOpen(false); setQ(""); }

  async function createItem(kind) {
    if (!query || busy) return;
    setBusy(true);
    try {
      const created = await api.post("/items", {
        name: query, kind, unit: kind === "SERVICE" ? "خدمت" : "عدد",
      });
      if (reloadItems) reloadItems();
      onChange(String(created.id));
      setOpen(false); setQ("");
    } catch (e) {
      alert(e.message || "خطا در ثبت مورد جدید");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ position: "relative", minWidth: 170 }}>
      <input
        value={open ? q : (selected ? selected.name : "")}
        placeholder="جستجوی کالا/خدمت…"
        onFocus={() => { setOpen(true); setQ(""); }}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onBlur={() => setTimeout(() => setOpen(false), 180)}
      />
      {open && (
        <div style={{
          position: "absolute", zIndex: 60, insetInlineStart: 0, insetInlineEnd: 0,
          marginTop: 4, background: "#fff", border: "1px solid var(--line)",
          borderRadius: 10, boxShadow: "var(--shadow-pop)", maxHeight: 240, overflowY: "auto",
        }}>
          {matches.map((it) => (
            <div key={it.id} onMouseDown={(e) => { e.preventDefault(); choose(it.id); }}
              style={{ padding: "8px 10px", cursor: "pointer", display: "flex",
                justifyContent: "space-between", gap: 8, alignItems: "center" }}>
              <span>{it.name}</span>
              <span className={`badge ${it.kind === "GOODS" ? "blue" : "green"}`}
                style={{ fontSize: 10 }}>{it.kind_display}</span>
            </div>
          ))}
          {matches.length === 0 && !query && (
            <div style={{ padding: "8px 10px", color: "var(--muted)" }}>موردی نیست</div>
          )}
          {allowCreate && query && !exact && (
            <div style={{ borderTop: matches.length ? "1px solid var(--line-2)" : "none", padding: "8px 10px" }}>
              <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>
                «{query}» یافت نشد — افزودن به‌عنوان:
              </div>
              <div className="flex" style={{ gap: 6 }}>
                <button type="button" className="btn sm" disabled={busy}
                  onMouseDown={(e) => { e.preventDefault(); createItem("GOODS"); }}>+ کالا</button>
                <button type="button" className="btn sm" disabled={busy}
                  onMouseDown={(e) => { e.preventDefault(); createItem("SERVICE"); }}>+ خدمت</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
