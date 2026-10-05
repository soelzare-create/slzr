import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, toman, jalali } from "../api";
import { Modal, StatusBadge, useList, useOptions, useItems, ItemPicker } from "../components.jsx";
import { Avatar, Icon, Menu } from "../ui.jsx";
import { KindSplit } from "./Proformas.jsx";

export default function Purchases() {
  const { data, loading, error, reload, setError } = useList("/purchases");
  const suppliers = useOptions("/parties?role=supplier");
  const invoices = useOptions("/invoices?type=GOODS");
  const { items, reload: reloadItems } = useItems();
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState(null); // null = creating a new purchase
  const [form, setForm] = useState(blank());
  const [params, setParams] = useSearchParams();

  useEffect(() => {
    const sid = params.get("supplier");
    const iid = params.get("invoice");
    if (sid || iid) {
      setForm((f) => ({ ...f, ...(sid ? { supplier: sid } : {}), ...(iid ? { sale_invoice: iid } : {}) }));
      setOpen(true);
      params.delete("supplier"); params.delete("invoice");
      setParams(params, { replace: true });
    }
  }, []); // eslint-disable-line

  function blank() {
    return { supplier: "", sale_invoice: "", notes: "", lines: [emptyLine()] };
  }
  function emptyLine() {
    return { item: "", description: "", quantity: 1, unit_price: 0 };
  }

  function setLine(i, patch) {
    const lines = form.lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l));
    setForm({ ...form, lines });
  }

  function openNew() { setEditId(null); setForm(blank()); setOpen(true); }

  function startEdit(p) {
    setEditId(p.id);
    setForm({
      supplier: String(p.supplier),
      sale_invoice: p.sale_invoice ? String(p.sale_invoice) : "",
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
        supplier: Number(form.supplier),
        sale_invoice: form.sale_invoice ? Number(form.sale_invoice) : null,
        notes: form.notes,
        lines: form.lines.filter((l) => l.item).map((l) => ({
          item: Number(l.item), description: l.description,
          quantity: Number(l.quantity), unit_price: Number(l.unit_price),
        })),
      };
      if (editId) await api.put(`/purchases/${editId}`, payload);
      else await api.post("/purchases", payload);
      closeModal(); reload();
    } catch (err) { setError(err.message); }
  }

  async function act(id, action) {
    try { await api.post(`/purchases/${id}/${action}`); reload(); }
    catch (err) { setError(err.message); }
  }

  function menuFor(p) {
    const items = [];
    if (p.status === "DRAFT") {
      items.push({ label: "ثبت خرید", icon: "check", color: "#10a86b", onClick: () => act(p.id, "register") });
      items.push({ label: "ویرایش", icon: "edit", onClick: () => startEdit(p) });
    }
    if (p.status !== "CANCELLED") {
      items.push({ sep: true });
      items.push({ label: "ابطال", icon: "close", color: "#e0483d", onClick: () => act(p.id, "cancel") });
    }
    return items;
  }

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">خریدها</h1>
          <div className="page-sub">{data.length} خرید</div>
        </div>
        <button className="btn primary" onClick={openNew}>+ خرید جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? <div className="empty">در حال بارگذاری…</div> : (
        <div className="cards-grid">
          {data.map((p) => (
            <div className="pcard" key={p.id}>
              <div className="flex" style={{ alignItems: "flex-start", gap: 12 }}>
                <Avatar name={p.supplier_name} size={46} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="mono" style={{ fontWeight: 600, fontSize: 15 }}>{p.number}</div>
                  <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 2 }}>{p.supplier_name}</div>
                </div>
                <Menu title="اقدامات با این خرید" items={menuFor(p)} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, margin: "13px 0 0" }}>
                <div className="metaline"><Icon name="calendar" size={14} />{jalali(p.date || p.created_at)}</div>
                <div className="metaline"><Icon name="invoice" size={14} />{p.sale_invoice_number || "بدون فاکتور مرتبط"}</div>
              </div>
              <div className="foot">
                <div>
                  <div style={{ fontSize: 11, color: "var(--muted-2)" }}>مبلغ کل</div>
                  <div className="num" style={{ fontWeight: 700, fontSize: 14 }}>{toman(p.total)}</div>
                  <KindSplit goods={p.goods_total} service={p.service_total} />
                </div>
                <StatusBadge status={p.status} display={p.status_display} kind="purchase" />
              </div>
            </div>
          ))}
          {data.length === 0 && <div className="empty">هنوز خریدی ثبت نشده.</div>}
        </div>
      )}

      {open && (
        <Modal title={editId ? "ویرایش خرید" : "خرید جدید"} onClose={closeModal} wide>
          <form onSubmit={save}>
            <div className="row">
              <div className="field">
                <label>تأمین‌کننده</label>
                <select value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} required>
                  <option value="">— انتخاب —</option>
                  {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="field">
                <label>فاکتور مرتبط (اختیاری)</label>
                <select value={form.sale_invoice} onChange={(e) => setForm({ ...form, sale_invoice: e.target.value })}>
                  <option value="">— بدون فاکتور (خرید مستقل) —</option>
                  {invoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>{inv.number} — {inv.customer_name}</option>
                  ))}
                </select>
              </div>
            </div>
            <LineTable items={items} reloadItems={reloadItems} lines={form.lines} setLine={setLine}
              onAdd={() => setForm({ ...form, lines: [...form.lines, emptyLine()] })}
              onRemove={(i) => setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) })} />
            <div className="field">
              <label>توضیحات</label>
              <textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <button className="btn primary">{editId ? "ذخیرهٔ تغییرات" : "ذخیره خرید"}</button>
            <span className="muted" style={{ marginInlineStart: 12 }}>پس از ذخیره، دکمهٔ «ثبت خرید» سند مالی می‌سازد.</span>
          </form>
        </Modal>
      )}
    </div>
  );
}

function LineTable({ items, reloadItems, lines, setLine, onAdd, onRemove }) {
  return (
    <div className="card" style={{ background: "#fafbfc" }}>
      <table className="line-items">
        <thead><tr><th>کالا/خدمت</th><th>شرح</th><th>تعداد</th><th>قیمت واحد</th><th></th></tr></thead>
        <tbody>
          {lines.map((l, i) => (
            <tr key={i}>
              <td style={{ minWidth: 190 }}>
                <ItemPicker items={items} value={l.item} reloadItems={reloadItems}
                  onChange={(id) => setLine(i, { item: id })} />
              </td>
              <td><input value={l.description} onChange={(e) => setLine(i, { description: e.target.value })} /></td>
              <td style={{ width: 80 }}><input type="number" min="0" value={l.quantity} onChange={(e) => setLine(i, { quantity: e.target.value })} /></td>
              <td style={{ width: 140 }}><input type="number" min="0" value={l.unit_price} onChange={(e) => setLine(i, { unit_price: e.target.value })} /></td>
              <td><button type="button" className="btn danger sm" onClick={() => onRemove(i)}>✕</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" className="btn sm" onClick={onAdd}>+ افزودن ردیف</button>
    </div>
  );
}
