import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { TICKET_STATUS_FA, SUPPORT_WRITE_ROLES } from "../labels";

// فاز ۶ — پشتیبانی/تیکتینگ. هر تیکت به یک مشتری و (اختیاری) به سریال دستگاه وصل است.
export default function Support() {
  const { me, loading } = useMe();
  const [tickets, setTickets] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [team, setTeam] = useState([]);
  const [units, setUnits] = useState([]); // serialized stock units (devices)
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const emptyForm = () => ({
    customer_id: "",
    device_unit_id: "",
    owner_id: "",
    title: "",
    description: "",
  });
  const [form, setForm] = useState(emptyForm);

  const canWrite = me && SUPPORT_WRITE_ROLES.includes(me.role);

  const customerName = useMemo(() => {
    const m = {};
    customers.forEach((c) => (m[c.id] = c.name));
    return m;
  }, [customers]);
  const memberName = useMemo(() => {
    const m = {};
    team.forEach((u) => (m[u.id] = u.name));
    return m;
  }, [team]);
  const unitSerial = useMemo(() => {
    const m = {};
    units.forEach((u) => (m[u.id] = u.serial_number));
    return m;
  }, [units]);

  function reload() {
    api.listTickets().then(setTickets).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!me) return;
    reload();
    api.listParties({ role: "customer" }).then(setCustomers).catch(() => {});
    api.listTeam().then(setTeam).catch(() => {});
    api
      .listStockItems()
      .then((all) => setUnits(all.filter((u) => u.serial_number)))
      .catch(() => {});
  }, [me]);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    if (!form.customer_id) return setError("مشتری را انتخاب کنید");
    setBusy(true);
    try {
      await api.createTicket({
        customer_id: Number(form.customer_id),
        device_unit_id: form.device_unit_id ? Number(form.device_unit_id) : null,
        owner_id: form.owner_id ? Number(form.owner_id) : null,
        title: form.title,
        description: form.description || null,
      });
      setForm(emptyForm());
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function changeStatus(id, status) {
    setError("");
    try {
      await api.updateTicket(id, { status });
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>پشتیبانی — تیکت‌ها</h2>
        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>عنوان</th>
              <th>مشتری</th>
              <th>دستگاه (سریال)</th>
              <th>مسئول</th>
              <th>وضعیت</th>
              {canWrite && <th>تغییر وضعیت</th>}
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.title}</td>
                <td>{customerName[t.customer_id] || `#${t.customer_id}`}</td>
                <td>{t.device_unit_id ? unitSerial[t.device_unit_id] || `#${t.device_unit_id}` : "—"}</td>
                <td>{t.owner_id ? memberName[t.owner_id] || `#${t.owner_id}` : "—"}</td>
                <td>
                  <span className="badge">{TICKET_STATUS_FA[t.status] || t.status}</span>
                </td>
                {canWrite && (
                  <td>
                    <select
                      value={t.status}
                      onChange={(e) => changeStatus(t.id, e.target.value)}
                      style={{ width: 140, marginTop: 0 }}
                    >
                      {Object.entries(TICKET_STATUS_FA).map(([k, v]) => (
                        <option key={k} value={k}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </td>
                )}
              </tr>
            ))}
            {tickets.length === 0 && (
              <tr>
                <td colSpan={canWrite ? 7 : 6} style={{ textAlign: "center", opacity: 0.6 }}>
                  تیکتی ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {canWrite && (
        <form className="card" style={{ marginTop: 20 }} onSubmit={onCreate}>
          <h2 style={{ marginTop: 0 }}>ثبت تیکت جدید</h2>
          <div className="grid2">
            <div>
              <label>مشتری *</label>
              <select
                required
                value={form.customer_id}
                onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              >
                <option value="">— انتخاب —</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>دستگاه (سریال) — اختیاری</label>
              <select
                value={form.device_unit_id}
                onChange={(e) => setForm({ ...form, device_unit_id: e.target.value })}
              >
                <option value="">— بدون دستگاه —</option>
                {units.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.serial_number}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>مسئول پیگیری — اختیاری</label>
              <select
                value={form.owner_id}
                onChange={(e) => setForm({ ...form, owner_id: e.target.value })}
              >
                <option value="">— بدون مسئول —</option>
                {team.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>عنوان *</label>
              <input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>
          </div>
          <label>شرح مشکل</label>
          <textarea
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            style={{ width: "100%", resize: "vertical" }}
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy} style={{ width: "auto", marginTop: 12 }}>
            {busy ? "در حال ثبت…" : "ثبت تیکت"}
          </button>
        </form>
      )}
      {!canWrite && error && <div className="error">{error}</div>}
    </Layout>
  );
}
