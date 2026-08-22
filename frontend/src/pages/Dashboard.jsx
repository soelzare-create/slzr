import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import {
  ROLE_FA,
  ACCOUNTING_ROLES,
  INVOICE_STATUS_FA,
  PURCHASE_STATUS_FA,
} from "../labels";

const fa = (n) => Number(n || 0).toLocaleString("fa-IR");

// A tiny dependency-free horizontal bar.
function Bar({ name, value, max, kind }) {
  const pct = max > 0 ? Math.max(2, (Math.abs(value) / max) * 100) : 0;
  return (
    <div className="bar-row">
      <div className="bar-name">{name}</div>
      <div className="bar-track">
        <div className={`bar-fill ${kind || ""}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="bar-val">{fa(value)}</div>
    </div>
  );
}

function StatusBreakdown({ data, labels }) {
  return (
    <div className="row" style={{ gap: 16, flexWrap: "wrap", marginTop: 4 }}>
      {["unpaid", "paid", "overdue"].map((k) => (
        <span key={k}>
          <span className="badge">{labels[k]}</span>{" "}
          <b>{fa(data[k])}</b>
        </span>
      ))}
      <span style={{ opacity: 0.7 }}>مجموع: {fa(data.total)}</span>
    </div>
  );
}

// Rich management dashboard (manager / accountant).
function Overview({ ov }) {
  const maxFin = Math.max(ov.finance.income, ov.finance.expense, 1);
  const maxDebt = Math.max(...ov.top_debtors.map((d) => d.balance), 1);
  const maxCred = Math.max(...ov.top_creditors.map((c) => -c.balance), 1);

  return (
    <>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>نمای کلی</h2>
        <div className="kpis">
          <div className="stat">
            <div className={`stat-num ${ov.finance.net < 0 ? "neg" : "pos"}`}>{fa(ov.finance.net)}</div>
            <div className="kpi-label">مانده‌ی خالص</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.finance.income)}</div>
            <div className="kpi-label">مجموع دخل</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.finance.expense)}</div>
            <div className="kpi-label">مجموع خرج</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.counts.open_tasks)}</div>
            <div className="kpi-label">ارجاعات باز</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.counts.customers)}</div>
            <div className="kpi-label">مشتری‌ها</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.counts.suppliers)}</div>
            <div className="kpi-label">تأمین‌کننده‌ها</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.counts.activities)}</div>
            <div className="kpi-label">فعالیت‌ها</div>
          </div>
          <div className="stat">
            <div className="stat-num">{fa(ov.counts.products)}</div>
            <div className="kpi-label">کالاها</div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>دخل و خرج</h2>
        <Bar name="دخل (فروش)" value={ov.finance.income} max={maxFin} kind="income" />
        <Bar name="خرج (خرید)" value={ov.finance.expense} max={maxFin} kind="expense" />
        <div style={{ marginTop: 14 }}>
          <h3 style={{ margin: "0 0 6px", color: "var(--navy)" }}>وضعیت فاکتورهای فروش</h3>
          <StatusBreakdown data={ov.invoices} labels={INVOICE_STATUS_FA} />
          <h3 style={{ margin: "16px 0 6px", color: "var(--navy)" }}>وضعیت اسناد خرید</h3>
          <StatusBreakdown data={ov.purchases} labels={PURCHASE_STATUS_FA} />
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>بیشترین طلب ما (بدهکاران)</h2>
        {ov.top_debtors.length === 0 ? (
          <p style={{ opacity: 0.6 }}>موردی نیست</p>
        ) : (
          ov.top_debtors.map((d) => (
            <Bar key={d.party_id} name={d.party_name || `#${d.party_id}`} value={d.balance} max={maxDebt} kind="income" />
          ))
        )}
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>بیشترین بدهی ما (بستانکاران)</h2>
        {ov.top_creditors.length === 0 ? (
          <p style={{ opacity: 0.6 }}>موردی نیست</p>
        ) : (
          ov.top_creditors.map((c) => (
            <Bar key={c.party_id} name={c.party_name || `#${c.party_id}`} value={-c.balance} max={maxCred} kind="expense" />
          ))
        )}
      </div>
    </>
  );
}

// Basic dashboard (non-financial roles): operational counts only.
function BasicCounts() {
  const [counts, setCounts] = useState({
    customers: null,
    suppliers: null,
    activities: null,
    products: null,
  });
  useEffect(() => {
    Promise.all([
      api.listParties({ role: "customer" }),
      api.listParties({ role: "supplier" }),
      api.listActivities(),
      api.listProductModels(),
    ])
      .then(([customers, suppliers, activities, products]) =>
        setCounts({
          customers: customers.length,
          suppliers: suppliers.length,
          activities: activities.length,
          products: products.length,
        })
      )
      .catch(() => {});
  }, []);
  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>نمای کلی</h2>
      <div className="row" style={{ gap: 16, marginTop: 8, flexWrap: "wrap" }}>
        <Link to="/customers" className="stat">
          <div className="stat-num">{counts.customers ?? "—"}</div>
          <div>مشتری‌ها</div>
        </Link>
        <Link to="/suppliers" className="stat">
          <div className="stat-num">{counts.suppliers ?? "—"}</div>
          <div>تأمین‌کننده‌ها</div>
        </Link>
        <Link to="/activities" className="stat">
          <div className="stat-num">{counts.activities ?? "—"}</div>
          <div>فعالیت‌ها</div>
        </Link>
        <Link to="/inventory" className="stat">
          <div className="stat-num">{counts.products ?? "—"}</div>
          <div>کالاها</div>
        </Link>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { me, loading } = useMe();
  const isFinance = me && ACCOUNTING_ROLES.includes(me.role);
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    if (!me) return;
    if (isFinance) api.reportsOverview().then(setOverview).catch(() => {});
    if (me.role === "manager") api.listUsers().then(setUsers).catch(() => {});
  }, [me, isFinance]);

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card" style={{ marginBottom: 20 }}>
        <h2 style={{ marginTop: 0 }}>خوش آمدید، {me.name}</h2>
        <p style={{ opacity: 0.75, margin: 0 }}>
          سیستم یکپارچه مدیریت فرآیند داران‌ایکس — «همه چیز سر جای خودش».
        </p>
      </div>

      {isFinance ? (
        overview ? (
          <Overview ov={overview} />
        ) : (
          <div className="card">در حال بارگذاری گزارش‌ها…</div>
        )
      ) : (
        <BasicCounts />
      )}

      {me.role === "manager" && (
        <div className="card" style={{ marginTop: 20 }}>
          <h2 style={{ marginTop: 0 }}>کاربران تیم</h2>
          <table>
            <thead>
              <tr>
                <th>شناسه</th>
                <th>نام</th>
                <th>نقش</th>
                <th>شماره تماس</th>
                <th>وضعیت</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.name}</td>
                  <td>{ROLE_FA[u.role] || u.role}</td>
                  <td>{u.phone}</td>
                  <td>{u.is_active ? "فعال" : "غیرفعال"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  );
}
