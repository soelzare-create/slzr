import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, toman } from "../api";
import { Modal, StatusBadge, useList, useOptions, useItems, ItemPicker } from "../components.jsx";
import { JalaliDatePicker } from "../ui.jsx";
import { useAuth } from "../auth.jsx";
import { KindSplit } from "./Proformas.jsx";

export default function Invoices() {
  const { data, loading, error, reload, setError } = useList("/invoices");
  const { can } = useAuth();
  const customers = useOptions("/parties?role=customer");
  const { items, reload: reloadItems } = useItems();
  const [open, setOpen] = useState(false);
  const [editingMeta, setEditingMeta] = useState(null); // invoice being metadata-edited
  const [form, setForm] = useState(blank());
  const [params, setParams] = useSearchParams();

  useEffect(() => {
    const cid = params.get("customer");
    if (cid) {
      setForm((f) => ({ ...f, customer: cid }));
      setOpen(true);
      params.delete("customer");
      setParams(params, { replace: true });
    }
  }, []); // eslint-disable-line

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
                  <td className="mono">
                    {toman(inv.total)}
                    <KindSplit goods={inv.goods_total} service={inv.service_total} />
                  </td>
                  <td><StatusBadge status={inv.status} display={inv.status_display} kind="invoice" /></td>
                  <td className="flex">
                    {can("sales.edit") && (
                      <button className="btn sm" onClick={() => setEditingMeta(inv)}>ویرایش</button>
                    )}
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
                <div className="field"><label>شروع دوره</label><JalaliDatePicker value={form.period_start} onChange={(d) => setForm({ ...form, period_start: d })} /></div>
                <div className="field"><label>پایان دوره</label><JalaliDatePicker value={form.period_end} onChange={(d) => setForm({ ...form, period_end: d })} /></div>
              </div>
            )}
            <div className="card" style={{ background: "#fafbfc" }}>
              <table className="line-items">
                <thead><tr><th>خدمت</th><th>شرح</th><th>تعداد</th><th>قیمت واحد</th><th></th></tr></thead>
                <tbody>
                  {form.lines.map((l, i) => (
                    <tr key={i}>
                      <td style={{ minWidth: 190 }}>
                        <ItemPicker items={items} value={l.item} reloadItems={reloadItems}
                          onChange={(id) => setLine(i, { item: id })} />
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

      {editingMeta && (
        <InvoiceMetaModal
          invoice={editingMeta}
          onClose={() => setEditingMeta(null)}
          onSaved={() => { setEditingMeta(null); reload(); }}
          onError={setError}
        />
      )}
    </div>
  );
}

// A finalized invoice's amounts/lines are immutable (they posted a journal
// entry). Only descriptive metadata — notes, date, support period — is editable.
function InvoiceMetaModal({ invoice, onClose, onSaved, onError }) {
  const [form, setForm] = useState({
    notes: invoice.notes || "",
    date: invoice.date || "",
    period_start: invoice.period_start || "",
    period_end: invoice.period_end || "",
  });
  const [error, setError] = useState(null);
  const isSupport = invoice.type === "SUPPORT";

  async function save(e) {
    e.preventDefault();
    try {
      const payload = { notes: form.notes, date: form.date || null };
      if (isSupport) {
        payload.period_start = form.period_start || null;
        payload.period_end = form.period_end || null;
      }
      await api.patch(`/invoices/${invoice.id}`, payload);
      onSaved();
    } catch (err) { setError(err.message); onError && onError(err.message); }
  }

  return (
    <Modal title={`ویرایش فاکتور ${invoice.number}`} onClose={onClose}>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}
        <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
          مبلغ، اقلام و مشتریِ فاکتور صادرشده تغییرناپذیر است (سند مالی ثبت شده). برای
          اصلاح مبلغ، فاکتور را «ابطال/مرجوعی» و دوباره صادر کنید. اینجا فقط اطلاعات
          توصیفی قابل ویرایش است.
        </p>
        <div className="field">
          <label>تاریخ</label>
          <JalaliDatePicker value={form.date} onChange={(d) => setForm({ ...form, date: d })} />
        </div>
        {isSupport && (
          <div className="row">
            <div className="field"><label>شروع دوره</label><JalaliDatePicker value={form.period_start} onChange={(d) => setForm({ ...form, period_start: d })} /></div>
            <div className="field"><label>پایان دوره</label><JalaliDatePicker value={form.period_end} onChange={(d) => setForm({ ...form, period_end: d })} /></div>
          </div>
        )}
        <div className="field">
          <label>یادداشت</label>
          <textarea rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </div>
        <button className="btn primary">ذخیرهٔ تغییرات</button>
      </form>
    </Modal>
  );
}
