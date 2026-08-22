import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { TASK_STATUS_FA } from "../labels";

// ارجاعات — internal task referrals between employees (replaces ticketing).
const fmt = (dt) => (dt ? String(dt).replace("T", " ").slice(0, 16) : "—");

export default function Referrals() {
  const { me, loading } = useMe();
  const [tab, setTab] = useState("assigned"); // assigned | created
  const [tasks, setTasks] = useState([]);
  const [team, setTeam] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const emptyForm = () => ({
    assigned_to_id: "",
    title: "",
    description: "",
    scheduled_at: "",
  });
  const [form, setForm] = useState(emptyForm);

  const memberName = useMemo(() => {
    const m = {};
    team.forEach((u) => (m[u.id] = u.name));
    return m;
  }, [team]);

  function reload() {
    api.listTasks({ scope: tab }).then(setTasks).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!me) return;
    api.listTeam().then(setTeam).catch(() => {});
  }, [me]);

  useEffect(() => {
    if (me) reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, tab]);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    if (!form.assigned_to_id) return setError("کارمندِ ارجاع‌شونده را انتخاب کنید");
    setBusy(true);
    try {
      await api.createTask({
        assigned_to_id: Number(form.assigned_to_id),
        title: form.title,
        description: form.description || null,
        scheduled_at: form.scheduled_at || null,
      });
      setForm(emptyForm());
      if (tab !== "created") setTab("created");
      else reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function changeStatus(id, status) {
    setError("");
    try {
      await api.updateTask(id, { status });
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  const tabStyle = (t) => ({
    width: "auto",
    marginTop: 0,
    background: tab === t ? undefined : "transparent",
    color: tab === t ? undefined : "var(--navy)",
    border: "1px solid var(--navy)",
  });

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>ارجاعات</h2>
        <div className="row" style={{ gap: 8, marginBottom: 12 }}>
          <button style={tabStyle("assigned")} onClick={() => setTab("assigned")}>
            به من ارجاع شده
          </button>
          <button style={tabStyle("created")} onClick={() => setTab("created")}>
            من ارجاع داده‌ام
          </button>
        </div>

        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>عنوان</th>
              <th>{tab === "assigned" ? "ارجاع‌دهنده" : "مسئول انجام"}</th>
              <th>زمان انجام</th>
              <th>وضعیت</th>
              <th>انجام‌شده در</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => {
              const canAct = tab === "assigned" || me.role === "manager";
              return (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>
                    {t.title}
                    {t.description && (
                      <div style={{ opacity: 0.65, fontSize: 12 }}>{t.description}</div>
                    )}
                    {t.invoice_id && (
                      <div style={{ opacity: 0.6, fontSize: 12 }}>
                        مرتبط با فاکتور #{t.invoice_id}
                      </div>
                    )}
                  </td>
                  <td>
                    {tab === "assigned"
                      ? memberName[t.created_by_id] || `#${t.created_by_id}`
                      : memberName[t.assigned_to_id] || `#${t.assigned_to_id}`}
                  </td>
                  <td>{fmt(t.scheduled_at)}</td>
                  <td>
                    <span className="badge">{TASK_STATUS_FA[t.status] || t.status}</span>
                  </td>
                  <td>{fmt(t.done_at)}</td>
                  <td>
                    {canAct && (
                      <select
                        value={t.status}
                        onChange={(e) => changeStatus(t.id, e.target.value)}
                        style={{ width: 140, marginTop: 0 }}
                      >
                        {Object.entries(TASK_STATUS_FA).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                </tr>
              );
            })}
            {tasks.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", opacity: 0.6 }}>
                  موردی نیست
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <form className="card" style={{ marginTop: 20 }} onSubmit={onCreate}>
        <h2 style={{ marginTop: 0 }}>ارجاع کار جدید</h2>
        <div className="grid2">
          <div>
            <label>ارجاع به *</label>
            <select
              required
              value={form.assigned_to_id}
              onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}
            >
              <option value="">— انتخاب کارمند —</option>
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
              placeholder="مثلاً نصب و راه‌اندازی"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>
          <div>
            <label>زمان انجام (اختیاری)</label>
            <input
              type="datetime-local"
              value={form.scheduled_at}
              onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
            />
          </div>
        </div>
        <label>شرح</label>
        <textarea
          rows={3}
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          style={{ width: "100%", resize: "vertical" }}
        />
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={busy} style={{ width: "auto", marginTop: 12 }}>
          {busy ? "در حال ثبت…" : "ثبت ارجاع"}
        </button>
      </form>
    </Layout>
  );
}
