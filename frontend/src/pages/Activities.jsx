import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import SalesPanel from "../components/SalesPanel";
import {
  ACTIVITY_TYPE_FA,
  ACTIVITY_STATUS_FA,
  STAGE_FA,
  WRITE_ROLES,
} from "../labels";

const EMPTY = { customer_id: "", owner_id: "", type: "project", title: "" };

export default function Activities() {
  const { me, loading } = useMe();
  const [activities, setActivities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [team, setTeam] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [openId, setOpenId] = useState(null);
  const [salesId, setSalesId] = useState(null);

  const canWrite = me && WRITE_ROLES.includes(me.role);
  const custName = (id) => customers.find((c) => c.id === id)?.name || `#${id}`;
  const ownerName = (id) => team.find((u) => u.id === id)?.name || `#${id}`;

  function reload() {
    api
      .listActivities({ type: typeFilter })
      .then(setActivities)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!me) return;
    api.listParties({ role: "customer" }).then(setCustomers).catch(() => {});
    api.listTeam().then(setTeam).catch(() => {});
  }, [me]);

  useEffect(() => {
    if (me) reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, typeFilter]);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.createActivity({
        customer_id: Number(form.customer_id),
        owner_id: Number(form.owner_id),
        type: form.type,
        title: form.title || null,
      });
      setForm(EMPTY);
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>فعالیت‌ها</h2>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{ width: 200 }}
          >
            <option value="">همهٔ انواع</option>
            {Object.entries(ACTIVITY_TYPE_FA).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </div>

        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>عنوان</th>
              <th>مشتری</th>
              <th>مسئول</th>
              <th>نوع</th>
              <th>وضعیت</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {activities.map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td>
                <td>{a.title || "—"}</td>
                <td>{custName(a.customer_id)}</td>
                <td>{ownerName(a.owner_id)}</td>
                <td>{ACTIVITY_TYPE_FA[a.type]}</td>
                <td>
                  <span className="badge">{ACTIVITY_STATUS_FA[a.status]}</span>
                </td>
                <td>
                  <div className="row" style={{ gap: 6 }}>
                    {a.type === "project" && (
                      <button
                        className="secondary"
                        style={{ width: "auto", marginTop: 0, padding: "4px 10px" }}
                        onClick={() => setOpenId(openId === a.id ? null : a.id)}
                      >
                        مراحل
                      </button>
                    )}
                    <button
                      className="secondary"
                      style={{ width: "auto", marginTop: 0, padding: "4px 10px" }}
                      onClick={() => setSalesId(salesId === a.id ? null : a.id)}
                    >
                      پیش‌فاکتور/فاکتور
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {activities.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", opacity: 0.6 }}>
                  موردی نیست
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {openId && (
        <StagePanel
          activityId={openId}
          canWrite={me && ["manager", "sales", "technical"].includes(me.role)}
        />
      )}

      {salesId && (
        <SalesPanel activityId={salesId} canWrite={canWrite} onChanged={reload} />
      )}

      {canWrite && (
        <form className="card" style={{ marginTop: 20 }} onSubmit={onCreate}>
          <h2 style={{ marginTop: 0 }}>ثبت فعالیت جدید</h2>
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
              <label>مسئول *</label>
              <select
                required
                value={form.owner_id}
                onChange={(e) => setForm({ ...form, owner_id: e.target.value })}
              >
                <option value="">— انتخاب —</option>
                {team.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>نوع *</label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                {Object.entries(ACTIVITY_TYPE_FA).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>عنوان</label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy} style={{ width: "auto" }}>
            {busy ? "در حال ثبت…" : "ثبت فعالیت"}
          </button>
        </form>
      )}
    </Layout>
  );
}

function StagePanel({ activityId, canWrite }) {
  const [stages, setStages] = useState([]);
  const [stage, setStage] = useState("discovery");
  const [error, setError] = useState("");

  function reload() {
    api.getActivity(activityId).then((a) => setStages(a.stages)).catch(() => {});
  }
  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activityId]);

  async function add(e) {
    e.preventDefault();
    setError("");
    try {
      await api.addStage(activityId, { stage });
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <h2 style={{ marginTop: 0 }}>مراحل پروژه #{activityId}</h2>
      <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
        {stages.length === 0 && <span style={{ opacity: 0.6 }}>مرحله‌ای ثبت نشده</span>}
        {stages.map((s, i) => (
          <span key={s.id} className="badge">
            {i + 1}. {STAGE_FA[s.stage]}
          </span>
        ))}
      </div>
      {canWrite && (
        <form className="row" style={{ gap: 8, marginTop: 12 }} onSubmit={add}>
          <select value={stage} onChange={(e) => setStage(e.target.value)} style={{ width: 200 }}>
            {Object.entries(STAGE_FA).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <button type="submit" style={{ width: "auto", marginTop: 0 }}>
            افزودن مرحله
          </button>
        </form>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}
