import { useState } from "react";
import { api, toman } from "../api";
import { Modal, StatusBadge, useList, useOptions } from "../components.jsx";
import { useAuth } from "../auth.jsx";

export default function Invoices() {
  const { data, loading, error, reload, setError } = useList("/invoices");
  const { can } = useAuth();
  const customers = useOptions("/parties?role=customer");
  const items = useOptions("/items");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(blank());

  function blank() {
    return { type: "SERVICE", customer: "", period_start: "", period_end: "", notes: "", lines: [line()] };
  }
  function line() { return { item: "", description: "", quantity: 1, unit_price: 0 }; }
  function setLine(i, patch) {
    setForm({ ...form, lines: form.lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l)) });
  }

  async function save(e) {
    e.preventDefault();
    try {
      const payload = {
        type: form.type,
        customer: Number(form.customer),
        notes: form.notes,
        period_start: form.type === "SUPPORT" ? form.period_start || null : null,
        period_end: form.type === "SUPPORT" ? form.period_end || null : null,
        lines: form.lines.filter((l) => l.item).map((l) => ({
          item: Number(l.item), description: l.description,
          quantity: Number(l.quantity), unit_price: Number(l.unit_price),
        })),
      };
      await api.post("/technical/invoices", payload);
      setOpen(false); setForm(blank()); reload();
    } catch (err) { setError(err.message); }
  }

  async function reverse(id, returned) {
    try { await api.post(`/invoices/${id}/reverse`, { returned }); reload(); }
    catch (err) { setError(err.message); }
  }

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title">فاکتورها</h1>
        {can("technical.edit") && (
          <button className="btn primary" onClick={() => setOpen(true)}>+ فاکتور خدمات/پشتیبانی</button>
        )}
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>شماره</th><th>نوع</th><th>مشتری</th><th>مبلغ</th><th>وضعیت</th><th>عملیات</th></tr></thead>
            <tbody>
              {data.map((inv) => (
                <tr key={inv.id}>
                  <td className="mono">{inv.number}</td>
                  <td><span className="badge gray">{inv.type_display}</span></td>
                  <td>{inv.customer_name}</td>
                  <td className="mono">{toman(inv.total)}</td>
                  <td><StatusBadge status={inv.status} display={inv.status_display} kind="invoice" /></td>
                  <td className="flex">
                    {inv.status === "ISSUED" && (
                      <>
                        <button className="btn sm" onClick={() => reverse(inv.id, true)}>مرجوعی</button>
                        <button className="btn danger sm" onClick={() => reverse(inv.id, false)}>ابطال</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {data.length === 0 && <tr><td colSpan={6} className="empty">هنوز فاکتوری صادر نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
      <p className="muted" style={{ fontSize: 13 }}>
        فاکتور فروش کالا از مسیر «پیش‌فاکتور → تبدیل به فاکتور» ساخته می‌شود. اینجا فقط فاکتور خدمات و پشتیبانی ماهانه به‌صورت مستقیم صادر می‌شود.
      </p>

      {open && (
        <Modal title="فاکتور خدمات / پشتیبانی" onClose={() => setOpen(false)} wide>
          <form onSubmit={save}>
            <div className="row">
              <div className="field">
                <label>نوع فاکتور</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="SERVICE">خدمات</option>
                  <option value="SUPPORT">پشتیبانی ماهانه</option>
                </select>
              </div>
              <div className="field">
                <label>مشتری</label>
                <select value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} required>
                  <option value="">— انتخاب —</option>
                  {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            {form.type === "SUPPORT" && (
              <div className="row">
                <div className="field"><label>شروع دوره</label><input type="date" value={form.period_start} onChange={(e) => setForm({ ...form, period_start: e.target.value })} /></div>
                <div className="field"><label>پایان دوره</label><input type="date" value={form.period_end} onChange={(e) => setForm({ ...form, period_end: e.target.value })} /></div>
              </div>
            )}
            <div className="card" style={{ background: "#fafbfc" }}>
              <table className="line-items">
                <thead><tr><th>خدمت</th><th>شرح</th><th>تعداد</th><th>قیمت واحد</th><th></th></tr></thead>
                <tbody>
                  {form.lines.map((l, i) => (
                    <tr key={i}>
                      <td style={{ minWidth: 160 }}>
                        <select value={l.item} onChange={(e) => setLine(i, { item: e.target.value })}>
                          <option value="">— انتخاب —</option>
                          {items.map((it) => <option key={it.id} value={it.id}>{it.name}</option>)}
                        </select>
                      </td>
                      <td><input value={l.description} onChange={(e) => setLine(i, { description: e.target.value })} /></td>
                      <td style={{ width: 70 }}><input type="number" min="0" value={l.quantity} onChange={(e) => setLine(i, { quantity: e.target.value })} /></td>
                      <td style={{ width: 140 }}><input type="number" min="0" value={l.unit_price} onChange={(e) => setLine(i, { unit_price: e.target.value })} /></td>
                      <td><button type="button" className="btn danger sm" onClick={() => setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) })}>✕</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button type="button" className="btn sm" onClick={() => setForm({ ...form, lines: [...form.lines, line()] })}>+ افزودن ردیف</button>
            </div>
            <button className="btn primary">صدور فاکتور</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
