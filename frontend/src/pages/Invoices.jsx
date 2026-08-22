import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import {
  INVOICE_KIND_FA,
  INVOICE_STATUS_FA,
  WRITE_ROLES,
} from "../labels";

// A standalone list of every invoice (proforma + final) across all activities,
// with filters, status management, and issuing a new one from an activity.
export default function Invoices() {
  const { me, loading } = useMe();
  const [invoices, setInvoices] = useState([]);
  const [activities, setActivities] = useState([]);
  const [parties, setParties] = useState([]);
  const [team, setTeam] = useState([]);
  const [error, setError] = useState("");

  // filters
  const [kindFilter, setKindFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // create form
  const [activityId, setActivityId] = useState("");
  const [newKind, setNewKind] = useState("proforma");
  const [dueDate, setDueDate] = useState("");

  const canWrite = me && WRITE_ROLES.includes(me.role);

  function reload() {
    api
      .listInvoices({ kind: kindFilter, status: statusFilter })
      .then(setInvoices)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!me) return;
    api.listActivities().then(setActivities).catch(() => {});
    api.listParties().then(setParties).catch(() => {});
    api.listTeam().then(setTeam).catch(() => {});
  }, [me]);

  useEffect(() => {
    if (me) reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, kindFilter, statusFilter]);

  const activityById = (id) => activities.find((a) => a.id === id);
  const partyName = (id) => {
    const p = parties.find((x) => x.id === id);
    return p ? p.name : "—";
  };
  const customerOf = (activityId) => {
    const a = activityById(activityId);
    return a ? partyName(a.customer_id) : "—";
  };
  const issuerName = (id) => {
    const u = team.find((x) => x.id === id);
    return u ? u.name : `#${id}`;
  };
  const activityLabel = (a) =>
    `فعالیت #${a.id} — ${partyName(a.customer_id)}${a.title ? " — " + a.title : ""}`;

  async function issue(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createInvoice({
        activity_id: Number(activityId),
        kind: newKind,
        settlement_due_date: dueDate || null,
      });
      setActivityId("");
      setDueDate("");
      setNewKind("proforma");
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  async function finalize(id) {
    setError("");
    try {
      await api.finalizeInvoice(id);
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  async function setStatus(id, status) {
    setError("");
    try {
      await api.updateInvoice(id, { status });
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>فاکتورها</h2>

        {/* filters */}
        <div className="row" style={{ gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value)}
            style={{ width: 180 }}
          >
            <option value="">همه‌ی انواع</option>
            {Object.entries(INVOICE_KIND_FA).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ width: 180 }}
          >
            <option value="">همه‌ی وضعیت‌ها</option>
            {Object.entries(INVOICE_STATUS_FA).map(([k, v]) => (
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
              <th>مشتری</th>
              <th>نوع</th>
              <th>مبلغ</th>
              <th>وضعیت</th>
              <th>تاریخ تصفیه</th>
              <th>صادرکننده</th>
              {canWrite && <th>اقدام</th>}
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id}>
                <td>{inv.id}</td>
                <td>{customerOf(inv.activity_id)}</td>
                <td>
                  <span className="badge">{INVOICE_KIND_FA[inv.kind]}</span>
                </td>
                <td>{Number(inv.total_amount).toLocaleString("fa-IR")}</td>
                <td>{INVOICE_STATUS_FA[inv.status]}</td>
                <td>{inv.settlement_due_date || "—"}</td>
                <td>{issuerName(inv.issuer_id)}</td>
                {canWrite && (
                  <td>
                    <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                      {inv.kind === "proforma" && (
                        <button
                          style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => finalize(inv.id)}
                        >
                          نهایی‌سازی
                        </button>
                      )}
                      {inv.status !== "paid" ? (
                        <button
                          className="secondary"
                          style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => setStatus(inv.id, "paid")}
                        >
                          ثبت پرداخت
                        </button>
                      ) : (
                        <button
                          className="secondary"
                          style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => setStatus(inv.id, "unpaid")}
                        >
                          لغو پرداخت
                        </button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {invoices.length === 0 && (
              <tr>
                <td colSpan={canWrite ? 8 : 7} style={{ textAlign: "center", opacity: 0.6 }}>
                  فاکتوری یافت نشد
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {canWrite && (
        <form className="card" style={{ marginTop: 20 }} onSubmit={issue}>
          <h2 style={{ marginTop: 0 }}>صدور فاکتور جدید</h2>
          <p style={{ marginTop: 0, opacity: 0.75, fontSize: 14 }}>
            مبلغ فاکتور به‌طور خودکار از جمع اقلامِ فعالیت انتخاب‌شده محاسبه می‌شود.
            برای افزودن یا ویرایش اقلام، به صفحه‌ی «فعالیت‌ها» بروید.
          </p>
          <div className="grid2">
            <div>
              <label>فعالیت *</label>
              <select
                required
                value={activityId}
                onChange={(e) => setActivityId(e.target.value)}
              >
                <option value="">— انتخاب فعالیت —</option>
                {activities.map((a) => (
                  <option key={a.id} value={a.id}>
                    {activityLabel(a)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>نوع سند *</label>
              <select value={newKind} onChange={(e) => setNewKind(e.target.value)}>
                {Object.entries(INVOICE_KIND_FA).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>تاریخ تصفیه حساب</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={!activityId} style={{ width: "auto" }}>
            صدور
          </button>
        </form>
      )}

      {error && !canWrite && <div className="error">{error}</div>}
    </Layout>
  );
}
