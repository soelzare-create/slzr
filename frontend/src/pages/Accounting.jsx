import { useEffect, useState } from "react";
import { api, toman } from "../api";

const TYPE_FA = { ASSET: "دارایی", LIABILITY: "بدهی", EQUITY: "سرمایه", INCOME: "درآمد", EXPENSE: "هزینه" };

export default function Accounting() {
  const [tab, setTab] = useState("balance");
  return (
    <div>
      <h1 className="page-title">حسابداری</h1>
      <div className="toolbar">
        <div className="flex">
          <button className={`btn ${tab === "balance" ? "primary" : ""}`} onClick={() => setTab("balance")}>ترازنامه</button>
          <button className={`btn ${tab === "ledger" ? "primary" : ""}`} onClick={() => setTab("ledger")}>دفتر کل</button>
          <button className={`btn ${tab === "parties" ? "primary" : ""}`} onClick={() => setTab("parties")}>مانده طرف‌حساب‌ها</button>
          <button className={`btn ${tab === "journal" ? "primary" : ""}`} onClick={() => setTab("journal")}>اسناد</button>
        </div>
      </div>
      {tab === "balance" && <BalanceSheet />}
      {tab === "ledger" && <Ledger />}
      {tab === "parties" && <PartyBalances />}
      {tab === "journal" && <Journal />}
    </div>
  );
}

function useData(path) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { api.get(path).then(setData).catch((e) => setError(e.message)); }, [path]);
  return { data, error };
}

function BalanceSheet() {
  const { data, error } = useData("/reports/balance-sheet");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  return (
    <div className="row">
      <div className="card">
        <h3>ترازنامه</h3>
        <table>
          <tbody>
            <tr><td>دارایی‌ها</td><td className="mono">{toman(data.assets)}</td></tr>
            <tr><td>بدهی‌ها</td><td className="mono">{toman(data.liabilities)}</td></tr>
            <tr><td>سرمایه</td><td className="mono">{toman(data.equity)}</td></tr>
          </tbody>
        </table>
      </div>
      <div className="card">
        <h3>سود و زیان</h3>
        <table>
          <tbody>
            <tr><td>درآمد</td><td className="mono">{toman(data.income)}</td></tr>
            <tr><td>هزینه (بهای تمام‌شده)</td><td className="mono">{toman(data.expense)}</td></tr>
            <tr><td><b>سود خالص</b></td><td className="mono"><b>{toman(data.net_income)}</b></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Ledger() {
  const { data, error } = useData("/reports/ledger");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  return (
    <div className="card">
      <table>
        <thead><tr><th>کد</th><th>حساب</th><th>نوع</th><th>بدهکار</th><th>بستانکار</th><th>مانده</th></tr></thead>
        <tbody>
          {data.filter((r) => r.debit || r.credit).map((r) => (
            <tr key={r.code}>
              <td className="mono">{r.code}</td>
              <td>{r.name}</td>
              <td>{TYPE_FA[r.type]}</td>
              <td className="mono">{toman(r.debit)}</td>
              <td className="mono">{toman(r.credit)}</td>
              <td className="mono">{toman(r.balance)}</td>
            </tr>
          ))}
          {data.every((r) => !r.debit && !r.credit) && <tr><td colSpan={6} className="empty">هنوز سندی ثبت نشده.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function PartyBalances() {
  const { data, error } = useData("/reports/party-balances");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  return (
    <div className="card">
      <table>
        <thead><tr><th>طرف‌حساب</th><th>مانده</th><th>وضعیت</th></tr></thead>
        <tbody>
          {data.map((r) => (
            <tr key={r.party_id}>
              <td>{r.party_name}</td>
              <td className="mono">{toman(Math.abs(r.balance))}</td>
              <td>
                {r.balance > 0 ? <span className="badge blue">بدهکار به ما</span>
                  : r.balance < 0 ? <span className="badge amber">طلبکار از ما</span>
                  : <span className="badge gray">تسویه</span>}
              </td>
            </tr>
          ))}
          {data.length === 0 && <tr><td colSpan={3} className="empty">موردی نیست.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function Journal() {
  const { data, error } = useData("/journal");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  const entries = Array.isArray(data) ? data : data.results || [];
  return (
    <div>
      {entries.map((e) => (
        <div className="card" key={e.id}>
          <div className="toolbar" style={{ marginBottom: 8 }}>
            <b className="mono">{e.number} — {e.description}</b>
            <span className="muted">{e.date} {e.is_reversal && <span className="badge amber">سند برگشت</span>}</span>
          </div>
          <table>
            <thead><tr><th>حساب</th><th>طرف‌حساب</th><th>بدهکار</th><th>بستانکار</th></tr></thead>
            <tbody>
              {e.lines.map((l) => (
                <tr key={l.id}>
                  <td>{l.account_code} — {l.account_name}</td>
                  <td>{l.party_name || "—"}</td>
                  <td className="mono">{Number(l.debit) ? toman(l.debit) : "—"}</td>
                  <td className="mono">{Number(l.credit) ? toman(l.credit) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      {entries.length === 0 && <div className="card"><div className="empty">هنوز سندی ثبت نشده.</div></div>}
    </div>
  );
}
