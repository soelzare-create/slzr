import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import {
  FINANCIAL_TYPE_FA,
  PAYMENT_DIRECTION_FA,
  INVOICE_STATUS_FA,
  ACCOUNTING_ROLES,
} from "../labels";

const fa = (n) => Number(n || 0).toLocaleString("fa-IR");
const today = () => new Date().toISOString().slice(0, 10);

export default function Accounting() {
  const { me, loading } = useMe();
  const [summary, setSummary] = useState(null);
  const [balances, setBalances] = useState([]);
  const [docs, setDocs] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [payments, setPayments] = useState([]);
  const [activities, setActivities] = useState([]);
  const [parties, setParties] = useState([]);
  const [error, setError] = useState("");

  // receipt form (per invoice)
  const [receiptFor, setReceiptFor] = useState(null); // invoice
  const [amount, setAmount] = useState("");
  const [paidAt, setPaidAt] = useState(today());

  const allowed = me && ACCOUNTING_ROLES.includes(me.role);

  const partyName = useMemo(() => {
    const m = {};
    parties.forEach((p) => (m[p.id] = p.name));
    balances.forEach((b) => (m[b.party_id] = b.party_name));
    return m;
  }, [parties, balances]);

  const customerOf = (activityId) => {
    const a = activities.find((x) => x.id === activityId);
    return a ? partyName[a.customer_id] || `#${a.customer_id}` : "—";
  };

  function reload() {
    api.accountingSummary().then(setSummary).catch((e) => setError(e.message));
    api.accountingBalances().then(setBalances).catch(() => {});
    api.accountingDocuments().then(setDocs).catch(() => {});
    api.listInvoices({ kind: "final" }).then(setInvoices).catch(() => {});
    api.listPurchases().then(setPurchases).catch(() => {});
    api.listPayments().then(setPayments).catch(() => {});
  }

  useEffect(() => {
    if (!me || !allowed) return;
    api.listActivities().then(setActivities).catch(() => {});
    api.listParties().then(setParties).catch(() => {});
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, allowed]);

  const receivables = invoices.filter((i) => Number(i.remaining) > 0.0001);

  function openReceipt(inv) {
    setReceiptFor(inv);
    setAmount(String(inv.remaining));
    setPaidAt(today());
    setError("");
  }

  async function saveReceipt(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createPayment({
        direction: "receipt",
        invoice_id: receiptFor.id,
        amount: Number(amount),
        paid_at: paidAt || null,
      });
      setReceiptFor(null);
      setAmount("");
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

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
        <div className="row" style={{ gap: 16, flexWrap: "wrap" }}>
          <div className="stat">
            <div className="stat-num">{summary ? fa(summary.income) : "—"}</div>
            <div>مجموع فروش</div>
          </div>
          <div className="stat">
            <div className="stat-num">{summary ? fa(summary.received) : "—"}</div>
            <div>دریافت‌شده</div>
          </div>
          <div className="stat">
            <div className="stat-num" style={{ color: "#b45309" }}>
              {summary ? fa(summary.receivable) : "—"}
            </div>
            <div>طلبِ وصول‌نشده</div>
          </div>
          <div className="stat">
            <div className="stat-num">{summary ? fa(summary.expense) : "—"}</div>
            <div>مجموع خرید</div>
          </div>
          <div className="stat">
            <div className="stat-num">{summary ? fa(summary.paid_out) : "—"}</div>
            <div>پرداخت‌شده</div>
          </div>
          <div className="stat">
            <div className="stat-num" style={{ color: "#b45309" }}>
              {summary ? fa(summary.payable) : "—"}
            </div>
            <div>بدهیِ پرداخت‌نشده</div>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {/* Receivables: unpaid / partially-paid sales invoices */}
      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>طلب‌های وصول‌نشده (دریافت از مشتری)</h2>
        <table>
          <thead>
            <tr>
              <th>فاکتور</th>
              <th>مشتری</th>
              <th>مبلغ کل</th>
              <th>دریافت‌شده</th>
              <th>باقی‌مانده</th>
              <th>وضعیت</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {receivables.map((inv) => (
              <tr key={inv.id}>
                <td>#{inv.id}</td>
                <td>{customerOf(inv.activity_id)}</td>
                <td>{fa(inv.total_amount)}</td>
                <td>{fa(inv.paid_amount)}</td>
                <td style={{ fontWeight: 700, color: "#b45309" }}>{fa(inv.remaining)}</td>
                <td>
                  <span className="badge">{INVOICE_STATUS_FA[inv.status]}</span>
                </td>
                <td>
                  <button
                    style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                    onClick={() => openReceipt(inv)}
                  >
                    ثبت دریافت
                  </button>
                </td>
              </tr>
            ))}
            {receivables.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", opacity: 0.6 }}>
                  همه‌ی فاکتورها تسویه شده‌اند
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {receiptFor && (
          <form
            className="row"
            style={{ gap: 8, marginTop: 12, flexWrap: "wrap", alignItems: "flex-end" }}
            onSubmit={saveReceipt}
          >
            <div>
              <label style={{ margin: 0 }}>دریافت بابت فاکتور #{receiptFor.id}</label>
              <input
                type="number"
                min="0"
                step="any"
                placeholder="مبلغ دریافت"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{ width: 160 }}
                required
              />
            </div>
            <div>
              <label style={{ margin: 0 }}>تاریخ</label>
              <input type="date" value={paidAt} onChange={(e) => setPaidAt(e.target.value)} />
            </div>
            <button type="submit" style={{ width: "auto", marginTop: 0 }}>
              ثبت دریافت
            </button>
            <button
              type="button"
              className="secondary"
              style={{ width: "auto", marginTop: 0 }}
              onClick={() => setReceiptFor(null)}
            >
              انصراف
            </button>
          </form>
        )}
      </div>

      {/* Payments ledger */}
      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>دریافت‌ها و پرداخت‌ها</h2>
        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>نوع</th>
              <th>مبلغ</th>
              <th>تاریخ</th>
              <th>طرف‌حساب</th>
              <th>منبع</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>
                  <span className="badge">{PAYMENT_DIRECTION_FA[p.direction]}</span>
                </td>
                <td>{fa(p.amount)}</td>
                <td>{p.paid_at || "—"}</td>
                <td>{p.party_id ? partyName[p.party_id] || `#${p.party_id}` : "—"}</td>
                <td style={{ opacity: 0.75 }}>
                  {p.invoice_id
                    ? `فاکتور #${p.invoice_id}`
                    : p.purchase_id
                    ? `خرید #${p.purchase_id}`
                    : "—"}
                </td>
              </tr>
            ))}
            {payments.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", opacity: 0.6 }}>
                  تراکنشی ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>مانده‌ی طرف‌حساب‌ها</h2>
        <p style={{ opacity: 0.7, marginTop: 0 }}>
          مانده‌ی مثبت = طلبِ ما از او؛ مانده‌ی منفی = بدهیِ ما به او. (بر مبنای
          فاکتور/خرید ثبت‌شده)
        </p>
        <table>
          <thead>
            <tr>
              <th>طرف‌حساب</th>
              <th>فروش به او</th>
              <th>خرید از او</th>
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
        <h2 style={{ marginTop: 0 }}>دفتر اسناد مالی (تعهدی)</h2>
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
