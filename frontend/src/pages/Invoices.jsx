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

  function openPrint(k, docId) {
    window.open(`${location.origin}${location.pathname}#/print/${k}/${docId}`, "_blank");
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
          <button className="btn primary" onClick={() => setOpen(true)}>+ فاکتور جدید</button>
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
                    <button className="btn sm" onClick={() => openPrint("invoice", inv.id)}>چاپ</button>
                    {inv.type === "GOODS" && (
                      <button className="btn sm" onClick={() => openPrint("delivery", inv.id)}>حواله تحویل</button>
                    )}
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
        فاکتور فروش کالا با کنترل قانون ۵٪ و ثبت بهای‌تمام‌شده از مسیر «پیش‌فاکتور → تبدیل به فاکتور» ساخته می‌شود.
        فاکتور مستقیم اینجا (خدمات، پشتیبانی، یا فروش کالای بدون خرید مبدأ) فقط درآمد را ثبت می‌کند و بهای‌تمام‌شده ندارد.
      </p>

      {open && (
        <Modal title="صدور فاکتور" onClose={() => setOpen(false)} wide>
          <form onSubmit={save}>
            <div className="row">
              <div className="field">
                <label>نوع فاکتور</label>
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  <option value="GOODS">فروش کالا</option>
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

// Edit an invoice. Descriptive metadata (notes/date/period) is always editable.
// For an ISSUED invoice the line amounts (quantity/unit price) can also be
// changed — that re-posts the sale journal entry (reprice); goods lines from a
// proforma keep obeying the 5% rule. Items themselves are not changed here.
function InvoiceMetaModal({ invoice, onClose, onSaved, onError }) {
  const [form, setForm] = useState({
    notes: invoice.notes || "",
    date: invoice.date || "",
    period_start: invoice.period_start || "",
    period_end: invoice.period_end || "",
  });
  const [lines, setLines] = useState(
    (invoice.lines || []).map((l) => ({
      id: l.id, item_name: l.item_name, item_kind_display: l.item_kind_display,
      quantity: l.quantity, unit_price: l.unit_price, serials: l.serials || [],
    }))
  );
  const [error, setError] = useState(null);
  const isSupport = invoice.type === "SUPPORT";
  const canReprice = invoice.status === "ISSUED" && lines.length > 0;

  function setLine(i, patch) {
    setLines(lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));
  }
  function linesChanged() {
    return lines.some((l) => {
      const orig = (invoice.lines || []).find((o) => o.id === l.id);
      return orig && (Number(orig.quantity) !== Number(l.quantity) ||
        Number(orig.unit_price) !== Number(l.unit_price));
    });
  }
  const total = lines.reduce((s, l) => s + Number(l.quantity || 0) * Number(l.unit_price || 0), 0);

  async function save(e) {
    e.preventDefault();
    try {
      const payload = { notes: form.notes, date: form.date || null };
      if (isSupport) {
        payload.period_start = form.period_start || null;
        payload.period_end = form.period_end || null;
      }
      await api.patch(`/invoices/${invoice.id}`, payload);
      // Re-post the amounts only if the user actually changed a line.
      if (canReprice && linesChanged()) {
        await api.post(`/invoices/${invoice.id}/reprice`, {
          lines: lines.map((l) => ({
            id: l.id, quantity: Number(l.quantity), unit_price: Number(l.unit_price),
          })),
        });
      }
      onSaved();
    } catch (err) { setError(err.message); onError && onError(err.message); }
  }

  return (
    <Modal title={`ویرایش فاکتور ${invoice.number}`} onClose={onClose} wide>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}

        {canReprice ? (
          <>
            <label className="field" style={{ marginBottom: 6 }}>مبلغ و اقلام</label>
            <div className="card" style={{ background: "#fafbfc", marginBottom: 14 }}>
              <table className="line-items">
                <thead><tr><th>کالا/خدمت</th><th>دسته</th><th>تعداد</th><th>قیمت واحد</th><th>جمع</th><th>سریال‌ها</th></tr></thead>
                <tbody>
                  {lines.map((l, i) => (
                    <tr key={l.id}>
                      <td>{l.item_name}</td>
                      <td><span className="badge gray" style={{ fontSize: 10 }}>{l.item_kind_display}</span></td>
                      <td style={{ width: 80 }}><input type="number" min="0" value={l.quantity}
                        onChange={(e) => setLine(i, { quantity: e.target.value })} /></td>
                      <td style={{ width: 150 }}><input type="number" min="0" value={l.unit_price}
                        onChange={(e) => setLine(i, { unit_price: e.target.value })} /></td>
                      <td className="mono">{toman(Number(l.quantity || 0) * Number(l.unit_price || 0))}</td>
                      <td style={{ fontSize: 11.5 }}>
                        {(l.serials || []).length
                          ? (l.serials || []).map((s) => <span key={s} className="badge blue" style={{ fontSize: 10, marginInlineEnd: 3 }} dir="ltr">{s}</span>)
                          : <span className="muted">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ textAlign: "left", fontWeight: 700, marginTop: 6 }}>جمع کل: {toman(total)}</div>
            </div>
            <p className="muted" style={{ fontSize: 12.5, marginTop: 0 }}>
              تغییر مبلغ، سند حسابداری فاکتور را به‌روز می‌کند. برای فاکتور کالای برآمده از
              پیش‌فاکتور، قیمت هر قلم باید حداقل ۱٫۰۵ برابر قیمت خرید مبدأ باشد.
            </p>
          </>
        ) : (
          <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
            این فاکتور صادر نشده یا اقلامی ندارد؛ فقط اطلاعات توصیفی قابل ویرایش است.
          </p>
        )}

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
