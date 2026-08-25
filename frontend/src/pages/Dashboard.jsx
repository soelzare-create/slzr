import { useEffect, useState } from "react";
import { api, toman } from "../api";

const STATUS_FA = {
  DRAFT: "پیش‌نویس", CONFIRMED: "تأییدشده", AWAITING_PURCHASE: "منتظر خرید",
  READY: "آماده فاکتور", INVOICED: "فاکتورشده", CANCELLED: "ابطال", UNFULFILLABLE: "تأمین‌نشدنی",
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get("/dashboard").then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;

  return (
    <div>
      <h1 className="page-title">داشبورد</h1>
      <div className="kpis">
        <Kpi label="درآمد کل" value={toman(data.income)} />
        <Kpi label="مطالبات (دریافتنی)" value={toman(data.receivable)} />
        <Kpi label="بدهی (پرداختنی)" value={toman(data.payable)} />
        <Kpi label="پیش‌فاکتورهای باز" value={data.counts.open_proformas} />
      </div>

      <div className="row" style={{ marginTop: 18 }}>
        <div className="card">
          <h3>شمارش‌ها</h3>
          <table>
            <tbody>
              <tr><td>پیش‌فاکتورها</td><td className="mono">{data.counts.proformas}</td></tr>
              <tr><td>فاکتورها</td><td className="mono">{data.counts.invoices}</td></tr>
              <tr><td>خریدها</td><td className="mono">{data.counts.purchases}</td></tr>
            </tbody>
          </table>
        </div>
        <div className="card">
          <h3>وضعیت پیش‌فاکتورها</h3>
          <table>
            <tbody>
              {Object.entries(data.proforma_by_status)
                .filter(([, v]) => v > 0)
                .map(([k, v]) => (
                  <tr key={k}><td>{STATUS_FA[k] || k}</td><td className="mono">{v}</td></tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <div className="kpi">
      <div className="label">{label}</div>
      <div className="value mono">{value}</div>
    </div>
  );
}
