import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, toman } from "../api";
import { Modal, StatusBadge, useList, useOptions, useItems, ItemPicker } from "../components.jsx";
import { KindSplit } from "./Proformas.jsx";

export default function Purchases() {
  const { data, loading, error, reload, setError } = useList("/purchases");
  const suppliers = useOptions("/parties?role=supplier");
  const { items, reload: reloadItems } = useItems();
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState(null); // null = creating a new purchase
  const [form, setForm] = useState(blank());
  const [params, setParams] = useSearchParams();

  useEffect(() => {
    const sid = params.get("supplier");
    if (sid) {
      setForm((f) => ({ ...f, supplier: sid }));
      setOpen(true);
      params.delete("supplier");
      setParams(params, { replace: true });
    }
  }, []); // eslint-disable-line

  function blank() {
    return { supplier: "", notes: "", lines: [emptyLine()] };
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

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title">خریدها</h1>
        <button className="btn primary" onClick={openNew}>+ خرید جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>شماره</th><th>تأمین‌کننده</th><th>مبلغ</th><th>وضعیت</th><th>عملیات</th></tr></thead>
            <tbody>
              {data.map((p) => (
                <tr key={p.id}>
                  <td className="mono">{p.number}</td>
                  <td>{p.supplier_name}</td>
                  <td className="mono">
                    {toman(p.total)}
                    <KindSplit goods={p.goods_total} service={p.service_total} />
                  </td>
                  <td><StatusBadge status={p.status} display={p.status_display} kind="purchase" /></td>
                  <td className="flex">
                    {p.status === "DRAFT" && (
                      <button className="btn success sm" onClick={() => act(p.id, "register")}>ثبت خرید</button>
                    )}
                    {p.status === "DRAFT" && (
                      <button className="btn sm" onClick={() => startEdit(p)}>ویرایش</button>
                    )}
                    {p.status !== "CANCELLED" && (
                      <button className="btn danger sm" onClick={() => act(p.id, "cancel")}>ابطال</button>
                    )}
                  </td>
                </tr>
              ))}
              {data.length === 0 && <tr><td colSpan={5} className="empty">هنوز خریدی ثبت نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

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
