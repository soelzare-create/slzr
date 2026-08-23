import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { Donut, KpiCard, RankBars, Columns, fa } from "../components/Charts";
import {
  ROLE_FA,
  ACCOUNTING_ROLES,
  INVOICE_STATUS_FA,
  PURCHASE_STATUS_FA,
} from "../labels";

const TONE = {
  paid: "ok",
  partial: "info",
  unpaid: "warn",
  overdue: "bad",
};
const STATUS_COLOR = {
  paid: "var(--ok)",
  partial: "var(--sky)",
  unpaid: "var(--warn)",
  overdue: "var(--danger)",
};

function StatusLegend({ data, labels }) {
  return (
    <div className="legend">
      {["paid", "partial", "unpaid", "overdue"].map((k) => (
        <span className="legend-item" key={k}>
          <span className="dot" style={{ background: STATUS_COLOR[k] }} />
          <span style={{ color: "var(--text-2)" }}>{labels[k] || k}</span>
          <b>{fa(data[k])}</b>
        </span>
      ))}
      <span className="legend-item">
        <span style={{ color: "var(--text-2)" }}>مجموع</span>
        <b>{fa(data.total)}</b>
      </span>
    </div>
  );
}

// Rich management dashboard (manager / accountant).
function Overview({ ov, expenses }) {
  const receivable = ov.top_debtors.reduce((s, d) => s + Math.max(0, d.balance), 0);
  const payable = ov.top_creditors.reduce((s, c) => s + Math.max(0, -c.balance), 0);

  const invoiceSegments = ["paid", "partial", "unpaid", "overdue"].map((k) => ({
    label: INVOICE_STATUS_FA[k] || k,
    value: ov.invoices[k] || 0,
    color: STATUS_COLOR[k],
  }));

  const expenseItems = (expenses || [])
    .slice()
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 6)
    .map((e) => ({ name: e.category, value: e.amount }));

  return (
    <>
      <div className="kpis">
        <KpiCard
          label="مانده‌ی خالص"
          value={ov.finance.net}
          note="دخل منهای خرج"
          tone={ov.finance.net < 0 ? "bad" : "ok"}
        />
        <KpiCard label="مجموع دخل" value={ov.finance.income} note="فروش تعهدی" />
        <KpiCard label="مجموع خرج" value={ov.finance.expense} note="خرید تعهدی" />
        <KpiCard
          label="طلبِ وصول‌نشده"
          value={receivable}
          note={`${fa(ov.invoices.unpaid + ov.invoices.overdue)} فاکتور باز`}
          tone="warn"
        />
      </div>

      <div className="grid-cards" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="chart-head">
            <h2 style={{ margin: 0 }}>دخل و خرج</h2>
            <span className="hint">از ابتدای دوره</span>
          </div>
          <Columns
            groups={[
              {
                label: "دخل (فروش)",
                values: [
                  { label: "دخل", value: ov.finance.income, color: "var(--navy)" },
                ],
              },
              {
                label: "خرج (خرید)",
                values: [
                  { label: "خرج", value: ov.finance.expense, color: "var(--sky)" },
                ],
              },
              {
                label: "مانده",
                values: [
                  {
                    label: "مانده",
                    value: Math.abs(ov.finance.net),
                    color:
                      ov.finance.net < 0 ? "var(--danger)" : "var(--ok)",
                  },
                ],
              },
            ]}
          />
          <div
            style={{
              marginTop: 18,
              paddingTop: 16,
              borderTop: "1px solid var(--line-soft)",
              display: "flex",
              justifyContent: "space-between",
              fontSize: 12.5,
              color: "var(--text-2)",
            }}
          >
            <span>
              دخل <b className="num" style={{ color: "var(--text)" }}>{fa(ov.finance.income)}</b>
            </span>
            <span>
              خرج <b className="num" style={{ color: "var(--text)" }}>{fa(ov.finance.expense)}</b>
            </span>
            <span>
              مانده{" "}
              <b
                className="num"
                style={{ color: ov.finance.net < 0 ? "var(--danger)" : "var(--ok)" }}
              >
                {fa(ov.finance.net)}
              </b>
            </span>
          </div>
        </div>

        <div className="card">
          <div className="chart-head">
            <h2 style={{ margin: 0 }}>وضعیت فاکتورهای فروش</h2>
            <Link to="/invoices" style={{ fontSize: 12.5 }}>
              فاکتورها
            </Link>
          </div>
          <div style={{ marginTop: 16 }}>
            <Donut
              segments={invoiceSegments}
              centerValue={fa(ov.invoices.total)}
              centerLabel="فاکتور"
            />
          </div>
          <div
            style={{
              marginTop: 16,
              paddingTop: 14,
              borderTop: "1px solid var(--line-soft)",
            }}
          >
            <div style={{ fontSize: 12.5, color: "var(--text-2)" }}>
              وضعیت اسناد خرید
            </div>
            <StatusLegend data={ov.purchases} labels={PURCHASE_STATUS_FA} />
          </div>
        </div>
      </div>

      <div className="grid-cards" style={{ marginTop: 16 }}>
        <div className="card">
          <div className="chart-head">
            <h2 style={{ margin: 0 }}>بیشترین طلب ما</h2>
            <span className="hint num">{fa(receivable)}</span>
          </div>
          <div style={{ marginTop: 16 }}>
            <RankBars
              items={ov.top_debtors.map((d) => ({
                key: d.party_id,
                name: d.party_name || `#${d.party_id}`,
                value: d.balance,
              }))}
            />
          </div>
        </div>

        <div className="card">
          <div className="chart-head">
            <h2 style={{ margin: 0 }}>بیشترین بدهی ما</h2>
            <span className="hint num">{fa(payable)}</span>
          </div>
          <div style={{ marginTop: 16 }}>
            <RankBars
              items={ov.top_creditors.map((c) => ({
                key: c.party_id,
                name: c.party_name || `#${c.party_id}`,
                value: -c.balance,
              }))}
              color="var(--sky)"
            />
          </div>
          <div
            style={{
              marginTop: 18,
              paddingTop: 16,
              borderTop: "1px solid var(--line-soft)",
              fontSize: 12.5,
              color: "var(--text-2)",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>بستانکاران</span>
            <Link to="/accounting">مشاهده حسابداری</Link>
          </div>
        </div>
      </div>

      {expenseItems.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="chart-head">
            <h2 style={{ margin: 0 }}>هزینه‌ها بر اساس دسته</h2>
            <span className="hint">پرداخت‌های خروجی</span>
          </div>
          <div style={{ marginTop: 16 }}>
            <RankBars items={expenseItems} altColor="var(--sky)" />
          </div>
        </div>
      )}

      <div className="kpis" style={{ marginTop: 16 }}>
        <Link to="/customers" className="stat">
          <div className="kpi-label">مشتری‌ها</div>
          <div className="stat-num">{fa(ov.counts.customers)}</div>
        </Link>
        <Link to="/suppliers" className="stat">
          <div className="kpi-label">تأمین‌کننده‌ها</div>
          <div className="stat-num">{fa(ov.counts.suppliers)}</div>
        </Link>
        <Link to="/activities" className="stat">
          <div className="kpi-label">فعالیت‌ها</div>
          <div className="stat-num">{fa(ov.counts.activities)}</div>
        </Link>
        <Link to="/inventory" className="stat">
          <div className="kpi-label">مدل کالا</div>
          <div className="stat-num">{fa(ov.counts.products)}</div>
        </Link>
        <Link to="/referrals" className="stat">
          <div className="kpi-label">ارجاعات باز</div>
          <div className="stat-num">{fa(ov.counts.open_tasks)}</div>
        </Link>
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
    tasks: null,
  });
  useEffect(() => {
    Promise.all([
      api.listParties({ role: "customer" }),
      api.listParties({ role: "supplier" }),
      api.listActivities(),
      api.listProductModels(),
      api.listTasks({ scope: "assigned" }),
    ])
      .then(([customers, suppliers, activities, products, tasks]) =>
        setCounts({
          customers: customers.length,
          suppliers: suppliers.length,
          activities: activities.length,
          products: products.length,
          tasks: tasks.filter((t) => t.status !== "done").length,
        })
      )
      .catch(() => {});
  }, []);

  const cell = (to, label, v) => (
    <Link to={to} className="stat" key={to}>
      <div className="kpi-label">{label}</div>
      <div className="stat-num">{v == null ? "—" : fa(v)}</div>
    </Link>
  );

  return (
    <div className="kpis">
      {cell("/customers", "مشتری‌ها", counts.customers)}
      {cell("/suppliers", "تأمین‌کننده‌ها", counts.suppliers)}
      {cell("/activities", "فعالیت‌ها", counts.activities)}
      {cell("/inventory", "مدل کالا", counts.products)}
      {cell("/referrals", "ارجاعات باز من", counts.tasks)}
    </div>
  );
}

export default function Dashboard() {
  const { me, loading } = useMe();
  const isFinance = me && ACCOUNTING_ROLES.includes(me.role);
  const [overview, setOverview] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    if (!me) return;
    if (isFinance) {
      api.reportsOverview().then(setOverview).catch(() => {});
      api.expenseByCategory().then(setExpenses).catch(() => {});
    }
    if (me.role === "manager") api.listUsers().then(setUsers).catch(() => {});
  }, [me, isFinance]);

  if (loading || !me)
    return (
      <div className="container" style={{ color: "var(--text-2)" }}>
        در حال بارگذاری…
      </div>
    );

  return (
    <Layout me={me} subtitle={`خوش آمدید، ${me.name} — نمای کلی مالی و عملیاتی سازمان`}>
      {isFinance ? (
        overview ? (
          <Overview ov={overview} expenses={expenses} />
        ) : (
          <div className="card" style={{ color: "var(--text-2)" }}>
            در حال بارگذاری گزارش‌ها…
          </div>
        )
      ) : (
        <BasicCounts />
      )}

      {me.role === "manager" && (
        <div className="card" style={{ marginTop: 16, padding: 0 }}>
          <div
            style={{
              padding: "18px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <h2 style={{ margin: 0 }}>کاربران تیم</h2>
            <span className="hint" style={{ fontSize: 11.5, color: "var(--text-3)" }}>
              {fa(users.length)} کاربر
            </span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ marginTop: 0 }}>
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
                    <td className="num" style={{ color: "var(--text-3)" }}>{u.id}</td>
                    <td>{u.name}</td>
                    <td>
                      <span className="badge">{ROLE_FA[u.role] || u.role}</span>
                    </td>
                    <td className="num" style={{ color: "var(--text-2)" }}>{u.phone}</td>
                    <td>
                      <span className={`badge ${u.is_active ? "ok" : ""}`}>
                        {u.is_active ? "فعال" : "غیرفعال"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Layout>
  );
}
