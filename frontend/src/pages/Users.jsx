import { useEffect, useState } from "react";
import { api, rows } from "../api";
import { useAuth } from "../auth.jsx";
import { Modal, useOptions } from "../components.jsx";

// User (account) administration — creating employees/managers and assigning
// their roles. System-admin only (Section 3, decision #8).
export default function Users() {
  const { user } = useAuth();
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(null); // user object, {} for new, or null
  const roles = useOptions("/roles");

  function reload() {
    setLoading(true);
    api.get("/users")
      .then((d) => setList(rows(d)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { if (user?.is_system_admin) reload(); }, [user]);

  if (!user?.is_system_admin) {
    return (
      <div>
        <h1 className="page-title">حساب‌های کاربری</h1>
        <div className="card"><div className="empty">این بخش فقط برای ادمین سیستم در دسترس است.</div></div>
      </div>
    );
  }

  const roleName = (code) => roles.find((r) => r.code === code)?.name || code;

  async function toggleActive(u) {
    try { await api.patch(`/users/${u.id}`, { is_active: !u.is_active }); reload(); }
    catch (e) { setError(e.message); }
  }

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">حساب‌های کاربری</h1>
          <div className="page-sub">{list.length} کاربر — ساخت و مدیریت کاربران و نقش‌ها</div>
        </div>
        <button className="btn primary" onClick={() => setEditing({})}>+ کاربر جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>نام</th><th>شماره تماس</th><th>نقش‌ها</th><th>وضعیت</th><th></th></tr></thead>
            <tbody>
              {list.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}{u.is_system_admin && <span className="badge blue" style={{ marginInlineStart: 6 }}>ادمین سیستم</span>}</td>
                  <td dir="ltr" style={{ textAlign: "right" }}>{u.phone}</td>
                  <td>
                    <div className="flex" style={{ gap: 5, flexWrap: "wrap" }}>
                      {(u.role_codes || []).map((c) => <span key={c} className="badge gray">{roleName(c)}</span>)}
                      {(u.role_codes || []).length === 0 && !u.is_system_admin && <span className="muted">—</span>}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${u.is_active ? "green" : "red"}`}>{u.is_active ? "فعال" : "غیرفعال"}</span>
                  </td>
                  <td style={{ textAlign: "left" }}>
                    <div className="flex" style={{ gap: 6, justifyContent: "flex-end" }}>
                      <button className="btn sm" onClick={() => setEditing(u)}>ویرایش</button>
                      {u.id !== user.id && (
                        <button className="btn sm" onClick={() => toggleActive(u)}>
                          {u.is_active ? "غیرفعال‌سازی" : "فعال‌سازی"}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {list.length === 0 && <tr><td colSpan={5} className="empty">هنوز کاربری ثبت نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {editing && (
        <UserModal user={editing} roles={roles}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); reload(); }} />
      )}
    </div>
  );
}

function UserModal({ user, roles, onClose, onSaved }) {
  const isNew = !user.id;
  const initialRoleIds = (roles || [])
    .filter((r) => (user.role_codes || []).includes(r.code))
    .map((r) => r.id);
  const [form, setForm] = useState({
    full_name: user.full_name || "",
    phone: user.phone || "",
    password: "",
    is_active: user.is_active ?? true,
    is_system_admin: user.is_system_admin ?? false,
    role_ids: initialRoleIds,
  });
  const [error, setError] = useState(null);

  function toggleRole(id) {
    setForm((f) => ({
      ...f,
      role_ids: f.role_ids.includes(id)
        ? f.role_ids.filter((x) => x !== id)
        : [...f.role_ids, id],
    }));
  }

  async function save(e) {
    e.preventDefault();
    setError(null);
    try {
      const payload = {
        full_name: form.full_name,
        phone: form.phone,
        is_active: form.is_active,
        is_system_admin: form.is_system_admin,
        role_ids: form.role_ids,
      };
      if (form.password) payload.password = form.password;
      if (isNew) await api.post("/users", payload);
      else await api.patch(`/users/${user.id}`, payload);
      onSaved();
    } catch (err) { setError(err.message); }
  }

  // Group roles by department for a tidy checklist.
  const bySystem = {};
  (roles || []).forEach((r) => { (bySystem[r.system_code] = bySystem[r.system_code] || []).push(r); });

  return (
    <Modal title={isNew ? "کاربر جدید" : "ویرایش کاربر"} icon="users" onClose={onClose} wide>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}
        <div className="row">
          <div className="field"><label>نام و نام خانوادگی</label>
            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></div>
          <div className="field"><label>شماره تماس (نام کاربری)</label>
            <input dir="ltr" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required /></div>
        </div>
        <div className="field">
          <label>رمز عبور {isNew ? "" : "(خالی = بدون تغییر)"}</label>
          <input type="password" value={form.password} placeholder={isNew ? "پیش‌فرض: changeme123" : "••••••••"}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>

        <label className="field" style={{ marginBottom: 6 }}>نقش‌ها</label>
        <div className="card" style={{ background: "#fafbfc", marginBottom: 14 }}>
          {Object.keys(bySystem).length === 0 && <div className="muted">نقشی تعریف نشده.</div>}
          {Object.entries(bySystem).map(([sys, rs]) => (
            <div key={sys} style={{ marginBottom: 8 }}>
              <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>{sys}</div>
              <div className="flex" style={{ gap: 14, flexWrap: "wrap" }}>
                {rs.map((r) => (
                  <label key={r.id} className="flex" style={{ gap: 6, fontSize: 13.5 }}>
                    <input type="checkbox" style={{ width: "auto" }}
                      checked={form.role_ids.includes(r.id)} onChange={() => toggleRole(r.id)} />
                    {r.name}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="row" style={{ marginBottom: 16 }}>
          <label className="flex" style={{ fontSize: 14 }}>
            <input type="checkbox" style={{ width: "auto" }} checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> فعال
          </label>
          <label className="flex" style={{ fontSize: 14 }}>
            <input type="checkbox" style={{ width: "auto" }} checked={form.is_system_admin}
              onChange={(e) => setForm({ ...form, is_system_admin: e.target.checked })} /> ادمین سیستم (دسترسی کامل)
          </label>
        </div>

        <button className="btn primary" style={{ width: "100%" }}>{isNew ? "افزودن کاربر" : "ذخیرهٔ تغییرات"}</button>
      </form>
    </Modal>
  );
}
