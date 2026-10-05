import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, rows, toman, jalali } from "../api";
import { Modal, StatusBadge, useList, useOptions, useItems, ItemPicker } from "../components.jsx";
import { Avatar, Icon, Menu } from "../ui.jsx";

export default function Proformas() {
  const { data, loading, error, reload, setError } = useList("/proformas");
  const customers = useOptions("/parties?role=customer");
  const { items, reload: reloadItems } = useItems();
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState(null); // null = creating a new proforma
  const [form, setForm] = useState(blank());
  const [params, setParams] = useSearchParams();

  // Deep link from a customer's 3-dot menu: ?customer=ID preopens the modal.
  useEffect(() => {
    const cid = params.get("customer");
    if (cid) {
      setForm((f) => ({ ...f, customer: cid }));
      setOpen(true);
      params.delete("customer");
      setParams(params, { replace: true });
    }
  }, []); // eslint-disable-line

  function blank() { return { customer: "", notes: "", lines: [emptyLine()] }; }
  function emptyLine() { return { item: "", description: "", quantity: 1, unit_price: 0 }; }
  function setLine(i, patch) {
    setForm({ ...form, lines: form.lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l)) });
  }

  function openNew() { setEditId(null); setForm(blank()); setOpen(true); }

  function startEdit(p) {
    setEditId(p.id);
    setForm({
      customer: String(p.customer),
      notes: p.notes || "",
      lines: (p.lines || []).map((l) => ({
        item: String(l.item), description: l.description || "",
        quantity: l.quantity, unit_price: l.unit_price,
      })),
    });
    setOpen(true);
  }

  function closeModal() { setOpen(false); setEditId(null); setForm(blank()); }

  async function save(e) {
    e.preventDefault();
    try {
      const payload = {
        customer: Number(form.customer),
        notes: form.notes,
        lines: form.lines.filter((l) => l.item).map((l) => ({
          item: Number(l.item), description: l.description,
          quantity: Number(l.quantity), unit_price: Number(l.unit_price),
        })),
      };
      if (editId) await api.put(`/proformas/${editId}`, payload);
      else await api.post("/proformas", payload);
      closeModal(); reload();
    } catch (err) { setError(err.message); }
  }

  async function act(id, action, body) {
    try { await api.post(`/proformas/${id}/${action}`, body); reload(); }
    catch (err) { setError(err.message); }
  }

  function openPrint(pid) {
    window.open(`${location.origin}${location.pathname}#/print/proforma/${pid}`, "_blank");
  }

  function menuFor(p) {
    const items = [{ label: "چاپ", icon: "doc", onClick: () => openPrint(p.id) }];
    if (p.status === "DRAFT") {
      items.push({ label: "ویرایش", icon: "edit", onClick: () => startEdit(p) });
      items.push({ label: "تبدیل به فاکتور", icon: "invoice", color: "#10a86b", onClick: () => act(p.id, "convert") });
      items.push({ sep: true });
      items.push({ label: "ابطال", icon: "close", color: "#e0483d", onClick: () => act(p.id, "cancel") });
    }
    return items;
  }

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">پیش‌فاکتورها</h1>
          <div className="page-sub">{data.length} پیش‌فاکتور</div>
        </div>
        <button className="btn primary" onClick={openNew}>+ پیش‌فاکتور جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? <div className="empty">در حال بارگذاری…</div> : (
        <div className="cards-grid">
          {data.map((p) => (
            <div className="pcard" key={p.id}>
              <div className="flex" style={{ alignItems: "flex-start", gap: 12 }}>
                <Avatar name={p.customer_name} size={46} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="mono" style={{ fontWeight: 600, fontSize: 15 }}>{p.number}</div>
                  <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 2 }}>{p.customer_name}</div>
                </div>
                <Menu title="اقدامات با این پیش‌فاکتور" items={menuFor(p)} />
              </div>
              <div style={{ margin: "13px 0 0" }}>
                <div className="metaline"><Icon name="calendar" size={14} />{jalali(p.created_at)}</div>
              </div>
              <div className="foot">
                <div>
                  <div style={{ fontSize: 11, color: "var(--muted-2)" }}>مبلغ کل</div>
                  <div className="num" style={{ fontWeight: 700, fontSize: 14 }}>{toman(p.total)}</div>
                  <KindSplit goods={p.goods_total} service={p.service_total} />
                </div>
                <StatusBadge status={p.status} display={p.status_display} />
              </div>
            </div>
          ))}
          {data.length === 0 && <div className="empty">هنوز پیش‌فاکتوری ثبت نشده.</div>}
        </div>
      )}

      {open && (
        <Modal title={editId ? "ویرایش پیش‌فاکتور" : "پیش‌فاکتور جدید"} onClose={closeModal} wide>
          <form onSubmit={save}>
            <div className="row">
              <div className="field">
                <label>مشتری</label>
                <select value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} required>
                  <option value="">— انتخاب —</option>
                  {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <div className="card" style={{ background: "#fafbfc" }}>
              <table className="line-items">
                <thead><tr><th>کالا/خدمت</th><th>تعداد</th><th>قیمت فروش</th><th></th></tr></thead>
                <tbody>
                  {form.lines.map((l, i) => (
                    <tr key={i}>
                      <td style={{ minWidth: 190 }}>
                        <ItemPicker items={items} value={l.item} reloadItems={reloadItems}
                          onChange={(id) => setLine(i, { item: id })} />
                      </td>
                      <td style={{ width: 70 }}><input type="number" min="0" value={l.quantity} onChange={(e) => setLine(i, { quantity: e.target.value })} /></td>
                      <td style={{ width: 150 }}><input type="number" min="0" value={l.unit_price} onChange={(e) => setLine(i, { unit_price: e.target.value })} /></td>
                      <td><button type="button" className="btn danger sm" onClick={() => setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) })}>✕</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button type="button" className="btn sm" onClick={() => setForm({ ...form, lines: [...form.lines, emptyLine()] })}>+ افزودن ردیف</button>
            </div>
            <p className="muted" style={{ fontSize: 13 }}>
              با «تبدیل به فاکتور»، فاکتور فروش صادر و درخواست خرید برای بازرگانی ارسال می‌شود.
            </p>
            <button className="btn primary">{editId ? "ذخیرهٔ تغییرات" : "ذخیره پیش‌فاکتور"}</button>
          </form>
        </Modal>
      )}
    </div>
  );
}

// Small کالا/خدمت breakdown under a record's total, shown only when it mixes both.
export function KindSplit({ goods, service }) {
  const g = Number(goods || 0);
  const s = Number(service || 0);
  if (g <= 0 || s <= 0) return null;
  return (
    <div className="flex" style={{ gap: 5, marginTop: 3 }}>
      <span className="badge blue" style={{ fontSize: 10 }}>کالا {toman(g)}</span>
      <span className="badge green" style={{ fontSize: 10 }}>خدمت {toman(s)}</span>
    </div>
  );
}
