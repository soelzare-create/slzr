import { api, jalali } from "../api";
import { useList } from "../components.jsx";
import { Icon } from "../ui.jsx";

const META = {
  READY_TO_INVOICE: { icon: "check", color: "#10a86b", bg: "#e5f6ee" },
  PURCHASE_REQUEST: { icon: "cart", color: "#e0912f", bg: "#fdeee0" },
  RESERVATION_RELEASED: { icon: "calendar", color: "#2f6bff", bg: "#eaf0ff" },
  UNFULFILLABLE: { icon: "alert", color: "#e0483d", bg: "#fbe8e6" },
  SUPPORT_DUE: { icon: "bell", color: "#2f6bff", bg: "#eaf0ff" },
  GENERAL: { icon: "bell", color: "#5b6577", bg: "#eef1f7" },
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
          <div className="page-sub">رویدادهای مربوط به کارهای شما</div>
        </div>
        <button className="btn sm" onClick={readAll}>خواندن همه</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card" style={{ padding: "6px 20px 10px" }}>
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <tbody>
              {data.map((n) => {
                const m = META[n.kind] || META.GENERAL;
                return (
                  <tr key={n.id} style={n.is_read ? { opacity: 0.5 } : undefined}>
                    <td style={{ width: 46 }}>
                      <div className="avatar" style={{ width: 34, height: 34, borderRadius: 10, background: m.bg }}>
                        <Icon name={m.icon} size={16} color={m.color} />
                      </div>
                    </td>
                    <td>
                      <div style={{ fontSize: 13.5 }}>{n.message}</div>
                      <div className="muted" style={{ fontSize: 11.5 }}>{n.kind_display} · {jalali(n.created_at)}</div>
                    </td>
                    <td style={{ width: 90, textAlign: "left" }}>
                      {n.is_read
                        ? <span className="badge gray">خوانده‌شده</span>
                        : <button className="btn sm" onClick={() => markRead(n.id)}>خواندم</button>}
                    </td>
                  </tr>
                );
              })}
              {data.length === 0 && <tr><td className="empty">اعلانی وجود ندارد.</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
