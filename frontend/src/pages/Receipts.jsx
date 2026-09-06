import { useEffect, useState } from "react";
import { api, rows } from "../api";
import { useAuth } from "../auth.jsx";
import { Modal } from "../components.jsx";

// Warehouse intake (ورود به انبار): the warehouse physically receives the goods
// of a registered purchase and enters the serial numbers of the units.
export default function Receipts() {
  const { can } = useAuth();
  const [receivable, setReceivable] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [receiving, setReceiving] = useState(null); // a purchase object to receive

  function reload() {
    setLoading(true);
    Promise.all([
      api.get("/receipts/receivable").then(rows).catch(() => []),
      api.get("/receipts").then(rows).catch(() => []),
    ]).then(([rv, hist]) => { setReceivable(rv); setHistory(hist); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { if (can("warehouse.view")) reload(); }, []); // eslint-disable-line

  if (!can("warehouse.view")) {
    return (
      <div>
        <h1 className="page-title">ورود به انبار</h1>
        <div className="card"><div className="empty">این بخش برای کاربران انبار در دسترس است.</div></div>
      </div>
    );
  }

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">ورود به انبار</h1>
          <div className="page-sub">تحویل فیزیکی کالاهای خریداری‌شده و ثبت سریال‌ها</div>
        </div>
      </div>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>خریدهای در انتظار تحویل</h3>
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>شماره خرید</th><th>تأمین‌کننده</th><th>اقلام</th><th>وضعیت</th><th></th></tr></thead>
            <tbody>
              {receivable.map((p) => (
                <tr key={p.id}>
                  <td className="mono">{p.number}</td>
                  <td>{p.supplier_name}</td>
                  <td>{p.lines.length} قلم</td>
                  <td>
                    <span className={`badge ${p.received ? "green" : "amber"}`}>
                      {p.received ? "تحویل‌شده" : "در انتظار تحویل"}
                    </span>
                  </td>
                  <td style={{ textAlign: "left" }}>
                    {can("warehouse.edit") && (
                      <button className="btn sm primary" onClick={() => setReceiving(p)}>
                        {p.received ? "ثبت رسید دیگر" : "ثبت رسید"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {receivable.length === 0 && <tr><td colSpan={5} className="empty">خرید ثبت‌شده‌ای برای تحویل نیست.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h3 style={{ marginTop: 0 }}>رسیدهای ثبت‌شده</h3>
        <table>
          <thead><tr><th>شماره رسید</th><th>خرید</th><th>تأمین‌کننده</th><th>ثبت‌کننده</th><th>سریال‌ها</th></tr></thead>
          <tbody>
            {history.map((r) => {
              const serialCount = (r.items || []).reduce((s, it) => s + (it.serials || []).length, 0);
              return (
                <tr key={r.id}>
                  <td className="mono">{r.number}</td>
                  <td className="mono">{r.purchase_number}</td>
                  <td>{r.supplier_name}</td>
                  <td>{r.received_by_name}</td>
                  <td>{serialCount > 0 ? `${serialCount} سریال` : "—"}</td>
                </tr>
              );
            })}
            {history.length === 0 && <tr><td colSpan={5} className="empty">هنوز رسیدی ثبت نشده.</td></tr>}
          </tbody>
        </table>
      </div>

      {receiving && (
        <ReceiptModal purchase={receiving} onClose={() => setReceiving(null)}
          onSaved={() => { setReceiving(null); reload(); }} />
      )}
    </div>
  );
}

function ReceiptModal({ purchase, onClose, onSaved }) {
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState(
    (purchase.lines || []).map((l) => ({
      purchase_line: l.id, item_name: l.item_name, item_kind_display: l.item_kind_display,
      quantity: l.quantity, serialsText: "",
    }))
  );
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  function setLine(i, patch) {
    setLines(lines.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));
  }
  const parseSerials = (text) =>
    (text || "").split(/[\n,]+/).map((s) => s.trim()).filter(Boolean);

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/receipts", {
        purchase: purchase.id,
        notes,
        items: lines.map((l) => ({
          purchase_line: l.purchase_line,
          quantity: Number(l.quantity) || 0,
          serials: parseSerials(l.serialsText),
        })),
      });
      onSaved();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <Modal title={`ثبت رسید انبار — خرید ${purchase.number}`} icon="cart" onClose={onClose} wide>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}
        <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
          تعداد تحویل‌گرفته‌شده را تأیید و در صورت وجود، سریال هر واحد را وارد کنید
          (هر سریال در یک خط یا جداشده با کاما). سریال اختیاری است.
        </p>
        <div className="card" style={{ background: "#fafbfc" }}>
          <table className="line-items">
            <thead><tr><th>کالا/خدمت</th><th>دسته</th><th>تعداد</th><th>سریال‌ها (اختیاری)</th></tr></thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={l.purchase_line}>
                  <td>{l.item_name}</td>
                  <td><span className="badge gray" style={{ fontSize: 10 }}>{l.item_kind_display}</span></td>
                  <td style={{ width: 90 }}>
                    <input type="number" min="0" value={l.quantity}
                      onChange={(e) => setLine(i, { quantity: e.target.value })} />
                  </td>
                  <td>
                    <textarea rows={2} placeholder="SN-001، SN-002 …" value={l.serialsText}
                      onChange={(e) => setLine(i, { serialsText: e.target.value })} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="field">
          <label>توضیحات</label>
          <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button className="btn primary" disabled={busy}>{busy ? "در حال ثبت…" : "ثبت رسید انبار"}</button>
      </form>
    </Modal>
  );
}
