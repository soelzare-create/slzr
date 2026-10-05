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
        <div>
          <h1 className="page-title">اعلان‌ها</h1>
          <div className="page-sub">{data.length} اعلان</div>
        </div>
        <button className="btn sm" onClick={readAll}>خواندن همه</button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? <div className="empty">در حال بارگذاری…</div> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {data.map((n) => (
            <div className="pcard" key={n.id} style={n.is_read ? { opacity: 0.55 } : undefined}>
              <div className="flex" style={{ alignItems: "flex-start", gap: 12 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 12, background: "#eef1f7",
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0,
                }}>{ICON[n.kind] || "📌"}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14 }}>{n.message}</div>
                  <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>{n.kind_display}</div>
                </div>
                {!n.is_read && <button className="btn sm" onClick={() => markRead(n.id)}>خواندم</button>}
              </div>
            </div>
          ))}
          {data.length === 0 && <div className="empty">اعلانی وجود ندارد.</div>}
        </div>
      )}
    </div>
  );
}
