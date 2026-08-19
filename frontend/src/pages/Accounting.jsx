import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { FINANCIAL_TYPE_FA, ACCOUNTING_ROLES } from "../labels";

const fa = (n) => Number(n || 0).toLocaleString("fa-IR");

// فاز ۵ — حسابداری: خلاصه‌ی دخل/خرج، مانده‌ی هر طرف‌حساب، و دفتر اسناد مالی.
export default function Accounting() {
  const { me, loading } = useMe();
  const [summary, setSummary] = useState(null);
  const [balances, setBalances] = useState([]);
  const [docs, setDocs] = useState([]);
  const [error, setError] = useState("");

  const allowed = me && ACCOUNTING_ROLES.includes(me.role);

  // party id -> name, for labelling the ledger rows
  const partyName = useMemo(() => {
    const m = {};
    balances.forEach((b) => (m[b.party_id] = b.party_name));
    return m;
  }, [balances]);

  useEffect(() => {
    if (!me || !allowed) return;
    api.accountingSummary().then(setSummary).catch((e) => setError(e.message));
    api.accountingBalances().then(setBalances).catch(() => {});
    api.accountingDocuments().then(setDocs).catch(() => {});
  }, [me, allowed]);

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  if (!allowed) {
    return (
      <Layout me={me}>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>حسابداری</h2>
          <p style={{ opacity: 0.75 }}>
            این بخش فقط برای «مدیر» و «حسابدار» در دسترس است.
          </p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>حسابداری</h2>
        <div className="row" style={{ gap: 16 }}>
          <div className="stat">
            <div className="stat-num">{summary ? fa(summary.income) : "—"}</div>
            <div>مجموع دخل (فروش)</div>
          </div>
          <div className="stat">
            <div className="stat-num">{summary ? fa(summary.expense) : "—"}</div>
            <div>مجموع خرج (خرید)</div>
          </div>
          <div className="stat">
            <div className="stat-num" style={{ color: summary && summary.net < 0 ? "#b91c1c" : undefined }}>
              {summary ? fa(summary.net) : "—"}
            </div>
            <div>مانده‌ی خالص</div>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>مانده‌ی طرف‌حساب‌ها</h2>
        <p style={{ opacity: 0.7, marginTop: 0 }}>
          مانده‌ی مثبت = طلبِ ما از او؛ مانده‌ی منفی = بدهیِ ما به او.
        </p>
        <table>
          <thead>
            <tr>
              <th>طرف‌حساب</th>
              <th>دخل (فروش به او)</th>
              <th>خرج (خرید از او)</th>
              <th>مانده</th>
            </tr>
          </thead>
          <tbody>
            {balances.map((b) => (
              <tr key={b.party_id}>
                <td>{b.party_name || `#${b.party_id}`}</td>
                <td>{fa(b.income)}</td>
                <td>{fa(b.expense)}</td>
                <td style={{ fontWeight: 700, color: b.balance < 0 ? "#b91c1c" : "#15803d" }}>
                  {fa(b.balance)}
                </td>
              </tr>
            ))}
            {balances.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", opacity: 0.6 }}>
                  هنوز تراکنشی ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>دفتر اسناد مالی</h2>
        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>نوع</th>
              <th>مبلغ</th>
              <th>طرف‌حساب</th>
              <th>منبع</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.id}</td>
                <td>
                  <span className="badge">{FINANCIAL_TYPE_FA[d.type] || d.type}</span>
                </td>
                <td>{fa(d.amount)}</td>
                <td>{partyName[d.party_id] || (d.party_id ? `#${d.party_id}` : "—")}</td>
                <td style={{ opacity: 0.75 }}>
                  {d.invoice_id
                    ? `فاکتور #${d.invoice_id}`
                    : d.purchase_id
                    ? `خرید #${d.purchase_id}`
                    : "—"}
                </td>
              </tr>
            ))}
            {docs.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", opacity: 0.6 }}>
                  سندی ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
