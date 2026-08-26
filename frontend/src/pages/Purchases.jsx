import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api, toman } from "../api";
import { Modal, StatusBadge, useList, useOptions } from "../components.jsx";
import { Avatar, Icon } from "../ui.jsx";
import { useAuth } from "../auth.jsx";

const PAY_STATUS = {
  UNPAID: { cls: "red", label: "پرداخت‌نشده" },
  PARTIAL: { cls: "amber", label: "قسمتی" },
  PAID: { cls: "green", label: "تسویه‌شده" },
};

export default function Purchases() {
  const { data, loading, error, reload, setError } = useList("/purchases");
  const { can } = useAuth();
  const navigate = useNavigate();
  const suppliers = useOptions("/parties?role=supplier");
  const items = useOptions("/items");
  const [open, setOpen] = useState(false);
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
      await api.post("/purchases", payload);
      setOpen(false); setForm(blank()); reload();
    } catch (err) { setError(err.message); }
  }

  async function act(id, action) {
    try { await api.post(`/purchases/${id}/${action}`); reload(); }
    catch (err) { setError(err.message); }
  }

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">خریدها</h1>
          <div className="page-sub">ثبت خرید از تأمین‌کننده و اثر مالی خودکار</div>
        </div>
        <button className="btn primary" onClick={() => setOpen(true)}><Icon name="plus" size={16} color="#fff" /> خرید جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>شماره</th><th>تأمین‌کننده</th><th>مبلغ</th><th>پرداخت</th><th>وضعیت</th><th>عملیات</th></tr></thead>
            <tbody>
              {data.map((p) => {
                const ps = PAY_STATUS[p.payment_status] || PAY_STATUS.UNPAID;
                const canPay = p.status === "REGISTERED" && Number(p.remaining) > 0 && can("accounting.edit");
                return (
                <tr key={p.id}>
                  <td className="mono">{p.number}</td>
                  <td><div className="flex" style={{ gap: 10 }}><Avatar name={p.supplier_name} size={32} radius={9} />{p.supplier_name}</div></td>
                  <td className="mono">{toman(p.total)}</td>
                  <td>
                    {p.status === "REGISTERED"
                      ? <><span className={`badge ${ps.cls}`}>{ps.label}</span>
                          {p.payment_status === "PARTIAL" && <div className="muted num" style={{ fontSize: 11, marginTop: 2 }}>مانده: {toman(p.remaining)}</div>}</>
                      : <span className="muted">—</span>}
                  </td>
                  <td><StatusBadge status={p.status} display={p.status_display} kind="purchase" /></td>
                  <td className="flex" style={{ flexWrap: "wrap" }}>
                    {p.status === "DRAFT" && (
                      <button className="btn success sm" onClick={() => act(p.id, "register")}>ثبت خرید</button>
                    )}
                    {canPay && (
                      <button className="btn sm" onClick={() => navigate(`/accounting?doc=payment&party=${p.supplier}&purchase=${p.id}&amount=${p.remaining}`)}>پرداخت</button>
                    )}
                    {p.status !== "CANCELLED" && (
                      <button className="btn danger sm" onClick={() => act(p.id, "cancel")}>ابطال</button>
                    )}
                  </td>
                </tr>
                );
              })}
              {data.length === 0 && <tr><td colSpan={6} className="empty">هنوز خریدی ثبت نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {open && (
        <Modal title="خرید جدید" onClose={() => setOpen(false)} wide>
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
            <LineTable items={items} lines={form.lines} setLine={setLine}
              onAdd={() => setForm({ ...form, lines: [...form.lines, emptyLine()] })}
              onRemove={(i) => setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) })} />
            <div className="field">
              <label>توضیحات</label>
              <textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <button className="btn primary">ذخیره خرید</button>
            <span className="muted" style={{ marginInlineStart: 12 }}>پس از ذخیره، دکمهٔ «ثبت خرید» سند مالی می‌سازد.</span>
          </form>
        </Modal>
      )}
    </div>
  );
}

function LineTable({ items, lines, setLine, onAdd, onRemove }) {
  return (
    <div className="card" style={{ background: "#fafbfc" }}>
      <table className="line-items">
        <thead><tr><th>کالا/خدمت</th><th>شرح</th><th>تعداد</th><th>قیمت واحد</th><th></th></tr></thead>
        <tbody>
          {lines.map((l, i) => (
            <tr key={i}>
              <td style={{ minWidth: 160 }}>
                <select value={l.item} onChange={(e) => setLine(i, { item: e.target.value })}>
                  <option value="">— انتخاب —</option>
                  {items.map((it) => <option key={it.id} value={it.id}>{it.name}</option>)}
                </select>
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
