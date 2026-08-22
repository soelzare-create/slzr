import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import {
  FINANCIAL_TYPE_FA,
  PAYMENT_DIRECTION_FA,
  PAYMENT_METHOD_FA,
  CASH_ACCOUNT_TYPE_FA,
  CHEQUE_DIRECTION_FA,
  CHEQUE_STATUS_FA,
  INVOICE_STATUS_FA,
  EXPENSE_CATEGORIES,
  ACCOUNTING_ROLES,
} from "../labels";

const fa = (n) => Number(n || 0).toLocaleString("fa-IR");
const today = () => new Date().toISOString().slice(0, 10);

export default function Accounting() {
  const { me, loading } = useMe();
  const [summary, setSummary] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [balances, setBalances] = useState([]);
  const [docs, setDocs] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [payments, setPayments] = useState([]);
  const [expenseCats, setExpenseCats] = useState([]);
  const [cheques, setCheques] = useState([]);
  const [activities, setActivities] = useState([]);
  const [parties, setParties] = useState([]);
  const [voucher, setVoucher] = useState(null); // 'receipt' | 'payment' | null
  const [error, setError] = useState("");

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
  const accountName = (id) => accounts.find((a) => a.id === id)?.name || "—";

  function reload() {
    api.accountingSummary().then(setSummary).catch((e) => setError(e.message));
    api.listCashAccounts().then(setAccounts).catch(() => {});
    api.accountingBalances().then(setBalances).catch(() => {});
    api.accountingDocuments().then(setDocs).catch(() => {});
    api.listInvoices({ kind: "final" }).then(setInvoices).catch(() => {});
    api.listPurchases().then(setPurchases).catch(() => {});
    api.listPayments().then(setPayments).catch(() => {});
    api.expenseByCategory().then(setExpenseCats).catch(() => {});
    api.listCheques().then(setCheques).catch(() => {});
  }

  useEffect(() => {
    if (!me || !allowed) return;
    api.listActivities().then(setActivities).catch(() => {});
    api.listParties().then(setParties).catch(() => {});
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, allowed]);

  // purchase paid = sum of payments linked to it
  const purchasePaid = useMemo(() => {
    const m = {};
    payments.forEach((p) => {
      if (p.purchase_id) m[p.purchase_id] = (m[p.purchase_id] || 0) + Number(p.amount);
    });
    return m;
  }, [payments]);

  const receivables = invoices.filter((i) => Number(i.remaining) > 0.0001);
  const payables = purchases
    .map((p) => ({ ...p, remaining: Number(p.total_amount) - (purchasePaid[p.id] || 0) }))
    .filter((p) => p.remaining > 0.0001);

  const operatingExpense = useMemo(
    () =>
      payments
        .filter((p) => p.direction === "payment" && !p.purchase_id)
        .reduce((s, p) => s + Number(p.amount), 0),
    [payments]
  );
  const approxProfit = summary
    ? summary.income - summary.expense - operatingExpense
    : 0;

  async function afterSave() {
    setVoucher(null);
    reload();
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
      {/* KPIs */}
      <div className="card">
        <h2 style={{ marginTop: 0 }}>حسابداری</h2>
        <div className="row" style={{ gap: 16, flexWrap: "wrap" }}>
          <Stat label="موجودی نقدی کل" value={summary?.cash_on_hand} strong />
          <Stat label="فروش (تعهدی)" value={summary?.income} />
          <Stat label="دریافت‌شده" value={summary?.received} />
          <Stat label="طلبِ وصول‌نشده" value={summary?.receivable} warn />
          <Stat label="خرید (تعهدی)" value={summary?.expense} />
          <Stat label="پرداخت‌شده" value={summary?.paid_out} />
          <Stat label="بدهیِ پرداخت‌نشده" value={summary?.payable} warn />
          <Stat label="هزینه‌های عملیاتی" value={operatingExpense} />
          <Stat label="سود تقریبی" value={approxProfit} signed />
        </div>
        <div className="row" style={{ gap: 8, marginTop: 14, flexWrap: "wrap" }}>
          <button style={{ width: "auto", marginTop: 0 }} onClick={() => setVoucher("receipt")}>
            ثبت سند دریافت
          </button>
          <button style={{ width: "auto", marginTop: 0 }} onClick={() => setVoucher("payment")}>
            ثبت سند پرداخت / هزینه
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {voucher === "receipt" && (
        <ReceiptVoucher
          accounts={accounts}
          receivables={receivables}
          parties={parties.filter((p) => p.is_customer)}
          customerOf={customerOf}
          onSaved={afterSave}
          onCancel={() => setVoucher(null)}
        />
      )}
      {voucher === "payment" && (
        <PaymentVoucher
          accounts={accounts}
          payables={payables}
          parties={parties.filter((p) => p.is_supplier)}
          partyName={partyName}
          onSaved={afterSave}
          onCancel={() => setVoucher(null)}
        />
      )}

      {/* Cash & bank accounts */}
      <CashAccounts accounts={accounts} onChanged={reload} />

      {/* Receivables */}
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
              </tr>
            ))}
            {receivables.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: "center", opacity: 0.6 }}>
                  همه‌ی فاکتورها تسویه شده‌اند
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Payables */}
      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>بدهی‌های پرداخت‌نشده (پرداخت به تأمین‌کننده)</h2>
        <table>
          <thead>
            <tr>
              <th>خرید</th>
              <th>تأمین‌کننده</th>
              <th>مبلغ کل</th>
              <th>باقی‌مانده</th>
            </tr>
          </thead>
          <tbody>
            {payables.map((p) => (
              <tr key={p.id}>
                <td>#{p.id}</td>
                <td>{partyName[p.supplier_id] || `#${p.supplier_id}`}</td>
                <td>{fa(p.total_amount)}</td>
                <td style={{ fontWeight: 700, color: "#b45309" }}>{fa(p.remaining)}</td>
              </tr>
            ))}
            {payables.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", opacity: 0.6 }}>
                  بدهی پرداخت‌نشده‌ای نیست
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Cheques / installments */}
      <Cheques
        cheques={cheques}
        accounts={accounts}
        parties={parties}
        partyName={partyName}
        receivables={receivables}
        payables={payables}
        customerOf={customerOf}
        onChanged={reload}
      />

      {/* Expense by category */}
      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>هزینه‌ها بر اساس دسته</h2>
        <table>
          <thead>
            <tr>
              <th>دسته</th>
              <th>مبلغ</th>
            </tr>
          </thead>
          <tbody>
            {expenseCats.map((c) => (
              <tr key={c.category}>
                <td>{c.category}</td>
                <td>{fa(c.amount)}</td>
              </tr>
            ))}
            {expenseCats.length === 0 && (
              <tr>
                <td colSpan={2} style={{ textAlign: "center", opacity: 0.6 }}>
                  هنوز پرداختی ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Payments ledger */}
      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>دفتر دریافت‌ها و پرداخت‌ها</h2>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>شناسه</th>
                <th>نوع</th>
                <th>مبلغ</th>
                <th>تاریخ</th>
                <th>روش</th>
                <th>حساب</th>
                <th>طرف‌حساب</th>
                <th>بابت / دسته</th>
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
                  <td>{PAYMENT_METHOD_FA[p.method] || "—"}</td>
                  <td>{p.account_id ? accountName(p.account_id) : "—"}</td>
                  <td>{p.party_id ? partyName[p.party_id] || `#${p.party_id}` : "—"}</td>
                  <td style={{ opacity: 0.8 }}>
                    {p.invoice_id
                      ? `فاکتور #${p.invoice_id}`
                      : p.purchase_id
                      ? `خرید #${p.purchase_id}`
                      : p.category || (p.note ? p.note : "—")}
                  </td>
                </tr>
              ))}
              {payments.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", opacity: 0.6 }}>
                    سندی ثبت نشده
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Party balances */}
      <div className="card" style={{ marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>مانده‌ی طرف‌حساب‌ها</h2>
        <p style={{ opacity: 0.7, marginTop: 0 }}>
          مثبت = طلبِ ما از او؛ منفی = بدهیِ ما به او (بر مبنای فاکتور/خرید ثبت‌شده).
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

      {/* Accrual ledger */}
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

function Stat({ label, value, strong, warn, signed }) {
  const color = warn
    ? "#b45309"
    : signed && Number(value) < 0
    ? "#b91c1c"
    : signed
    ? "#15803d"
    : undefined;
  return (
    <div className="stat">
      <div className="stat-num" style={{ color, fontWeight: strong ? 800 : undefined }}>
        {value == null ? "—" : Number(value).toLocaleString("fa-IR")}
      </div>
      <div>{label}</div>
    </div>
  );
}

function CashAccounts({ accounts, onChanged }) {
  const [name, setName] = useState("");
  const [type, setType] = useState("cash");
  const [opening, setOpening] = useState("");
  const [error, setError] = useState("");
  const [show, setShow] = useState(false);

  async function add(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createCashAccount({
        name,
        type,
        opening_balance: opening ? Number(opening) : 0,
      });
      setName("");
      setOpening("");
      setShow(false);
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  const total = accounts.reduce((s, a) => s + Number(a.balance), 0);

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>صندوق و بانک</h2>
        <button
          className="secondary"
          style={{ width: "auto", marginTop: 0 }}
          onClick={() => setShow(!show)}
        >
          + حساب جدید
        </button>
      </div>
      <table style={{ marginTop: 10 }}>
        <thead>
          <tr>
            <th>نام</th>
            <th>نوع</th>
            <th>مانده‌ی اولیه</th>
            <th>مانده‌ی فعلی</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((a) => (
            <tr key={a.id}>
              <td>{a.name}</td>
              <td>{CASH_ACCOUNT_TYPE_FA[a.type] || a.type}</td>
              <td>{Number(a.opening_balance).toLocaleString("fa-IR")}</td>
              <td style={{ fontWeight: 700 }}>
                {Number(a.balance).toLocaleString("fa-IR")}
              </td>
            </tr>
          ))}
          {accounts.length === 0 && (
            <tr>
              <td colSpan={4} style={{ textAlign: "center", opacity: 0.6 }}>
                حسابی تعریف نشده — یکی بسازید تا اسناد به آن وصل شوند
              </td>
            </tr>
          )}
          {accounts.length > 0 && (
            <tr>
              <td colSpan={3} style={{ textAlign: "left", fontWeight: 700 }}>
                جمع موجودی
              </td>
              <td style={{ fontWeight: 800 }}>
                {Number(total).toLocaleString("fa-IR")}
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {show && (
        <form className="row" style={{ gap: 8, marginTop: 12, flexWrap: "wrap", alignItems: "flex-end" }} onSubmit={add}>
          <div>
            <label style={{ margin: 0 }}>نام حساب</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="مثلاً صندوق فروشگاه" />
          </div>
          <div>
            <label style={{ margin: 0 }}>نوع</label>
            <select value={type} onChange={(e) => setType(e.target.value)}>
              {Object.entries(CASH_ACCOUNT_TYPE_FA).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ margin: 0 }}>مانده‌ی اولیه</label>
            <input type="number" min="0" value={opening} onChange={(e) => setOpening(e.target.value)} />
          </div>
          <button type="submit" style={{ width: "auto", marginTop: 0 }}>ثبت حساب</button>
        </form>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}

function AccountAndMethod({ accounts, accountId, setAccountId, method, setMethod }) {
  return (
    <>
      <div>
        <label>حساب مالی</label>
        <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
          <option value="">— بدون حساب —</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label>روش</label>
        <select value={method} onChange={(e) => setMethod(e.target.value)}>
          {Object.entries(PAYMENT_METHOD_FA).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>
    </>
  );
}

function ReceiptVoucher({ accounts, receivables, parties, customerOf, onSaved, onCancel }) {
  const [mode, setMode] = useState("invoice"); // invoice | misc
  const [invoiceId, setInvoiceId] = useState("");
  const [partyId, setPartyId] = useState("");
  const [amount, setAmount] = useState("");
  const [paidAt, setPaidAt] = useState(today());
  const [method, setMethod] = useState("cash");
  const [accountId, setAccountId] = useState("");
  const [category, setCategory] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  function pickInvoice(id) {
    setInvoiceId(id);
    const inv = receivables.find((i) => String(i.id) === String(id));
    if (inv) setAmount(String(inv.remaining));
  }

  async function save(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createPayment({
        direction: "receipt",
        amount: Number(amount),
        paid_at: paidAt || null,
        method,
        account_id: accountId ? Number(accountId) : null,
        invoice_id: mode === "invoice" && invoiceId ? Number(invoiceId) : null,
        party_id: mode === "misc" && partyId ? Number(partyId) : null,
        category: mode === "misc" ? category || "دریافت متفرقه" : null,
        note: note || null,
      });
      onSaved();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <form className="card" style={{ marginTop: 16, border: "1px solid var(--navy)" }} onSubmit={save}>
      <h3 style={{ marginTop: 0 }}>سند دریافت</h3>
      <div className="row" style={{ gap: 8, marginBottom: 10 }}>
        <label style={{ margin: 0 }}>
          <input type="radio" checked={mode === "invoice"} onChange={() => setMode("invoice")} /> بابت فاکتور
        </label>
        <label style={{ margin: 0 }}>
          <input type="radio" checked={mode === "misc"} onChange={() => setMode("misc")} /> دریافت متفرقه
        </label>
      </div>
      <div className="grid2">
        {mode === "invoice" ? (
          <div>
            <label>فاکتور *</label>
            <select value={invoiceId} onChange={(e) => pickInvoice(e.target.value)} required>
              <option value="">— انتخاب فاکتور —</option>
              {receivables.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  #{inv.id} — {customerOf(inv.activity_id)} — باقی‌مانده {Number(inv.remaining).toLocaleString("fa-IR")}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <>
            <div>
              <label>طرف‌حساب (اختیاری)</label>
              <select value={partyId} onChange={(e) => setPartyId(e.target.value)}>
                <option value="">— بدون طرف‌حساب —</option>
                {parties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label>بابتِ</label>
              <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="مثلاً بیعانه / علی‌الحساب" />
            </div>
          </>
        )}
        <div>
          <label>مبلغ *</label>
          <input type="number" min="0" step="any" value={amount} onChange={(e) => setAmount(e.target.value)} required />
        </div>
        <div>
          <label>تاریخ</label>
          <input type="date" value={paidAt} onChange={(e) => setPaidAt(e.target.value)} />
        </div>
        <AccountAndMethod accounts={accounts} accountId={accountId} setAccountId={setAccountId} method={method} setMethod={setMethod} />
        <div>
          <label>شرح</label>
          <input value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="row" style={{ gap: 8, marginTop: 12 }}>
        <button type="submit" style={{ width: "auto" }}>ثبت دریافت</button>
        <button type="button" className="secondary" style={{ width: "auto", marginTop: 0 }} onClick={onCancel}>انصراف</button>
      </div>
    </form>
  );
}

function PaymentVoucher({ accounts, payables, parties, partyName, onSaved, onCancel }) {
  const [mode, setMode] = useState("expense"); // purchase | expense
  const [purchaseId, setPurchaseId] = useState("");
  const [partyId, setPartyId] = useState("");
  const [category, setCategory] = useState(EXPENSE_CATEGORIES[0]);
  const [amount, setAmount] = useState("");
  const [paidAt, setPaidAt] = useState(today());
  const [method, setMethod] = useState("cash");
  const [accountId, setAccountId] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  function pickPurchase(id) {
    setPurchaseId(id);
    const pur = payables.find((p) => String(p.id) === String(id));
    if (pur) setAmount(String(pur.remaining));
  }

  async function save(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createPayment({
        direction: "payment",
        amount: Number(amount),
        paid_at: paidAt || null,
        method,
        account_id: accountId ? Number(accountId) : null,
        purchase_id: mode === "purchase" && purchaseId ? Number(purchaseId) : null,
        party_id: mode === "expense" && partyId ? Number(partyId) : null,
        category: mode === "expense" ? category : null,
        note: note || null,
      });
      onSaved();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <form className="card" style={{ marginTop: 16, border: "1px solid var(--navy)" }} onSubmit={save}>
      <h3 style={{ marginTop: 0 }}>سند پرداخت / هزینه</h3>
      <div className="row" style={{ gap: 8, marginBottom: 10 }}>
        <label style={{ margin: 0 }}>
          <input type="radio" checked={mode === "expense"} onChange={() => setMode("expense")} /> هزینه‌ی عملیاتی
        </label>
        <label style={{ margin: 0 }}>
          <input type="radio" checked={mode === "purchase"} onChange={() => setMode("purchase")} /> بابت خرید
        </label>
      </div>
      <div className="grid2">
        {mode === "purchase" ? (
          <div>
            <label>خرید *</label>
            <select value={purchaseId} onChange={(e) => pickPurchase(e.target.value)} required>
              <option value="">— انتخاب سند خرید —</option>
              {payables.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} — {partyName[p.supplier_id] || `#${p.supplier_id}`} — باقی‌مانده {Number(p.remaining).toLocaleString("fa-IR")}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <>
            <div>
              <label>دستهٔ هزینه *</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {EXPENSE_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label>طرف‌حساب (اختیاری)</label>
              <select value={partyId} onChange={(e) => setPartyId(e.target.value)}>
                <option value="">— بدون طرف‌حساب —</option>
                {parties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          </>
        )}
        <div>
          <label>مبلغ *</label>
          <input type="number" min="0" step="any" value={amount} onChange={(e) => setAmount(e.target.value)} required />
        </div>
        <div>
          <label>تاریخ</label>
          <input type="date" value={paidAt} onChange={(e) => setPaidAt(e.target.value)} />
        </div>
        <AccountAndMethod accounts={accounts} accountId={accountId} setAccountId={setAccountId} method={method} setMethod={setMethod} />
        <div>
          <label>شرح</label>
          <input value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="row" style={{ gap: 8, marginTop: 12 }}>
        <button type="submit" style={{ width: "auto" }}>ثبت پرداخت</button>
        <button type="button" className="secondary" style={{ width: "auto", marginTop: 0 }} onClick={onCancel}>انصراف</button>
      </div>
    </form>
  );
}

function Cheques({ cheques, accounts, parties, partyName, receivables, payables, customerOf, onChanged }) {
  const [show, setShow] = useState(false);
  const [dir, setDir] = useState("received");
  const [number, setNumber] = useState("");
  const [bank, setBank] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState(today());
  const [partyId, setPartyId] = useState("");
  const [linkId, setLinkId] = useState(""); // invoice (received) or purchase (issued)
  const [accountId, setAccountId] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [clearing, setClearing] = useState(null); // cheque being cleared
  const [clearAccount, setClearAccount] = useState("");
  const [clearDate, setClearDate] = useState(today());

  const linkParties = parties.filter((p) =>
    dir === "received" ? p.is_customer : p.is_supplier
  );
  const todayStr = today();

  async function add(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createCheque({
        direction: dir,
        number,
        bank_name: bank || null,
        amount: Number(amount),
        due_date: dueDate,
        party_id: partyId ? Number(partyId) : null,
        invoice_id: dir === "received" && linkId ? Number(linkId) : null,
        purchase_id: dir === "issued" && linkId ? Number(linkId) : null,
        account_id: accountId ? Number(accountId) : null,
        note: note || null,
      });
      setNumber(""); setBank(""); setAmount(""); setPartyId(""); setLinkId(""); setNote("");
      setShow(false);
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  async function doClear(e) {
    e.preventDefault();
    setError("");
    try {
      await api.clearCheque(clearing.id, {
        account_id: clearAccount ? Number(clearAccount) : null,
        cleared_at: clearDate || null,
      });
      setClearing(null);
      setClearAccount("");
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  async function bounce(id) {
    setError("");
    try {
      await api.bounceCheque(id);
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  const dueStyle = (c) => {
    if (c.status !== "registered") return {};
    if (c.due_date < todayStr) return { color: "#b91c1c", fontWeight: 700 }; // گذشته
    return {};
  };

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>چک‌ها و اقساط</h2>
        <button className="secondary" style={{ width: "auto", marginTop: 0 }} onClick={() => setShow(!show)}>
          + ثبت چک
        </button>
      </div>
      <p style={{ opacity: 0.7, marginTop: 6, fontSize: 13 }}>
        برای پرداخت اقساطی، چند چک با سررسیدهای مختلف روی یک فاکتور/خرید ثبت کنید.
        با «وصول»، سند دریافت/پرداخت واقعی ساخته و فاکتور/خرید تسویه می‌شود.
      </p>

      {show && (
        <form className="card" style={{ background: "var(--bg-soft,#fafafa)" }} onSubmit={add}>
          <div className="row" style={{ gap: 8, marginBottom: 8 }}>
            <label style={{ margin: 0 }}>
              <input type="radio" checked={dir === "received"} onChange={() => { setDir("received"); setLinkId(""); setPartyId(""); }} /> دریافتی (از مشتری)
            </label>
            <label style={{ margin: 0 }}>
              <input type="radio" checked={dir === "issued"} onChange={() => { setDir("issued"); setLinkId(""); setPartyId(""); }} /> پرداختی (به تأمین‌کننده)
            </label>
          </div>
          <div className="grid2">
            <div><label>شماره چک *</label><input value={number} onChange={(e) => setNumber(e.target.value)} required /></div>
            <div><label>بانک</label><input value={bank} onChange={(e) => setBank(e.target.value)} /></div>
            <div><label>مبلغ *</label><input type="number" min="0" step="any" value={amount} onChange={(e) => setAmount(e.target.value)} required /></div>
            <div><label>سررسید *</label><input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required /></div>
            <div>
              <label>طرف‌حساب</label>
              <select value={partyId} onChange={(e) => setPartyId(e.target.value)}>
                <option value="">— بدون طرف‌حساب —</option>
                {linkParties.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label>{dir === "received" ? "بابت فاکتور (قسط)" : "بابت خرید (قسط)"}</label>
              <select value={linkId} onChange={(e) => setLinkId(e.target.value)}>
                <option value="">— بدون ارتباط —</option>
                {dir === "received"
                  ? receivables.map((inv) => (
                      <option key={inv.id} value={inv.id}>
                        فاکتور #{inv.id} — {customerOf(inv.activity_id)} — باقی‌مانده {Number(inv.remaining).toLocaleString("fa-IR")}
                      </option>
                    ))
                  : payables.map((p) => (
                      <option key={p.id} value={p.id}>
                        خرید #{p.id} — {partyName[p.supplier_id] || `#${p.supplier_id}`} — باقی‌مانده {Number(p.remaining).toLocaleString("fa-IR")}
                      </option>
                    ))}
              </select>
            </div>
            <div>
              <label>حساب وصول (اختیاری)</label>
              <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
                <option value="">— هنگام وصول انتخاب می‌شود —</option>
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div><label>شرح</label><input value={note} onChange={(e) => setNote(e.target.value)} /></div>
          </div>
          <button type="submit" style={{ width: "auto", marginTop: 10 }}>ثبت چک</button>
        </form>
      )}

      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>نوع</th>
              <th>شماره</th>
              <th>بانک</th>
              <th>مبلغ</th>
              <th>سررسید</th>
              <th>طرف‌حساب</th>
              <th>بابت</th>
              <th>وضعیت</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {cheques.map((c) => (
              <React.Fragment key={c.id}>
                <tr>
                  <td>{CHEQUE_DIRECTION_FA[c.direction]}</td>
                  <td>{c.number}</td>
                  <td>{c.bank_name || "—"}</td>
                  <td>{fa(c.amount)}</td>
                  <td style={dueStyle(c)}>{c.due_date}</td>
                  <td>{c.party_id ? partyName[c.party_id] || `#${c.party_id}` : "—"}</td>
                  <td style={{ opacity: 0.8 }}>
                    {c.invoice_id ? `فاکتور #${c.invoice_id}` : c.purchase_id ? `خرید #${c.purchase_id}` : "—"}
                  </td>
                  <td><span className="badge">{CHEQUE_STATUS_FA[c.status]}</span></td>
                  <td>
                    {c.status === "registered" && (
                      <div className="row" style={{ gap: 6 }}>
                        <button style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => { setClearing(c); setClearAccount(c.account_id ? String(c.account_id) : ""); setClearDate(today()); }}>
                          وصول
                        </button>
                        <button className="secondary" style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => bounce(c.id)}>
                          برگشت
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
                {clearing && clearing.id === c.id && (
                  <tr>
                    <td colSpan={9}>
                      <form className="row" style={{ gap: 8, flexWrap: "wrap", alignItems: "flex-end" }} onSubmit={doClear}>
                        <div>
                          <label style={{ margin: 0 }}>حساب مقصد *</label>
                          <select value={clearAccount} onChange={(e) => setClearAccount(e.target.value)} required>
                            <option value="">— انتخاب حساب —</option>
                            {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                          </select>
                        </div>
                        <div>
                          <label style={{ margin: 0 }}>تاریخ وصول</label>
                          <input type="date" value={clearDate} onChange={(e) => setClearDate(e.target.value)} />
                        </div>
                        <button type="submit" style={{ width: "auto", marginTop: 0 }}>تأیید وصول</button>
                        <button type="button" className="secondary" style={{ width: "auto", marginTop: 0 }} onClick={() => setClearing(null)}>انصراف</button>
                      </form>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {cheques.length === 0 && (
              <tr><td colSpan={9} style={{ textAlign: "center", opacity: 0.6 }}>چکی ثبت نشده</td></tr>
            )}
          </tbody>
        </table>
      </div>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
