import { api } from "../api";
import { useList } from "../components.jsx";

const ICON = {
  READY_TO_INVOICE: "✅", PURCHASE_REQUEST: "🛒", RESERVATION_RELEASED: "⏰",
  UNFULFILLABLE: "⚠️", SUPPORT_DUE: "🔔", GENERAL: "📌",
};

export default function Notifications() {
  const { data, loading, error, reload, setError } = useList("/notifications");

  async function markRead(id) {
    try { await api.post(`/notifications/${id}/read`); reload(); }
    catch (err) { setError(err.message); }
  }
  async function readAll() {
    try { await api.post("/notifications/read_all"); reload(); }
    catch (err) { setError(err.message); }
  }

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title">اعلان‌ها</h1>
        <button className="btn sm" onClick={readAll}>خواندن همه</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <tbody>
              {data.map((n) => (
                <tr key={n.id} style={n.is_read ? { opacity: 0.55 } : undefined}>
                  <td style={{ width: 40 }}>{ICON[n.kind] || "📌"}</td>
                  <td>
                    <div>{n.message}</div>
                    <div className="muted" style={{ fontSize: 12 }}>{n.kind_display}</div>
                  </td>
                  <td style={{ width: 110 }}>
                    {!n.is_read && <button className="btn sm" onClick={() => markRead(n.id)}>خواندم</button>}
                  </td>
                </tr>
              ))}
              {data.length === 0 && <tr><td className="empty">اعلانی وجود ندارد.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
