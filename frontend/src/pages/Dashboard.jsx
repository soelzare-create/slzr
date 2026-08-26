import { useEffect, useState } from "react";
import { api, toman, jalali } from "../api";
import { useAuth } from "../auth.jsx";
import { Avatar, Icon } from "../ui.jsx";

const STATUS_FA = {
  DRAFT: "پیش‌نویس", CONFIRMED: "تأییدشده", AWAITING_PURCHASE: "منتظر خرید",
  READY: "آماده فاکتور", INVOICED: "فاکتورشده", CANCELLED: "ابطال", UNFULFILLABLE: "تأمین‌نشدنی",
};
const STATUS_COLOR = {
  DRAFT: "#94a0b8", CONFIRMED: "#2f6bff", AWAITING_PURCHASE: "#e0912f",
  READY: "#10a86b", INVOICED: "#111c34", CANCELLED: "#e0483d", UNFULFILLABLE: "#e0483d",
};

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { api.get("/dashboard").then(setData).catch((e) => setError(e.message)); }, []);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;

  if (data.role === "sales") return <SalesDashboard data={data} user={user} />;
  if (data.role === "procurement") return <ProcurementDashboard data={data} user={user} />;
  if (data.role === "technical") return <TechnicalDashboard data={data} user={user} />;
  return <FinancialDashboard data={data} />;
}

function Kpi({ icon, iconBg, iconColor, label, value, trend, variant }) {
  return (
    <div className={`kpi ${variant || ""}`}>
      <div className="flex" style={{ justifyContent: "space-between" }}>
        <div className="ico" style={{ background: iconBg }}><Icon name={icon} size={19} color={iconColor} /></div>
        {trend && <span className="badge" style={{ background: variant ? "#ffffff22" : "#e5f6ee", color: variant ? "#fff" : "#10a86b" }}>{trend}</span>}
      </div>
      <div className="label" style={variant ? { color: "#d7e2ff" } : undefined}>{label}</div>
      <div className="value num">{value}</div>
    </div>
  );
}

function SalesDashboard({ data, user }) {
  return (
    <div>
      <h1 className="page-title">سلام {(user?.full_name || "").split(" ")[0]}</h1>
      <div className="page-sub" style={{ marginBottom: 18 }}>خلاصهٔ فروش و مطالبات شما</div>
      <div className="kpis" style={{ marginBottom: 16 }}>
        <Kpi variant="brand" icon="trend" iconBg="#ffffff22" iconColor="#fff" label="فروش من" value={toman(data.my_sales)} />
        <Kpi icon="coins" iconBg="#fbe8e6" iconColor="#e0483d" label="طلب وصول‌نشده" value={toman(data.uncollected)} />
        <Kpi icon="proforma" iconBg="#fdeee0" iconColor="#e0912f" label="پیش‌فاکتورهای باز" value={data.open_proformas} />
        <Kpi icon="target" iconBg="#e5f6ee" iconColor="#10a86b" label="نرخ تبدیل به فاکتور" value={`${data.conversion_rate}٪`} />
      </div>

      <div className="card">
        <div className="flex" style={{ gap: 8, marginBottom: 14 }}>
          <Icon name="alert" size={17} color="#e0483d" /><b style={{ fontSize: 15 }}>بدهکارترین مشتریان</b>
        </div>
        {(data.top_debtors || []).length === 0 ? <div className="empty">مطالبات معوقی ندارید.</div> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {data.top_debtors.map((d) => (
              <div className="flex" key={d.party_id} style={{ gap: 11 }}>
                <Avatar name={d.party_name} size={36} radius={11} />
                <div style={{ flex: 1 }}><div style={{ fontSize: 13.5, fontWeight: 600 }}>{d.party_name}</div></div>
                <div className="num" style={{ fontWeight: 700, fontSize: 13, color: "#e0483d" }}>{toman(d.balance)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ListCard({ icon, color, title, rows, empty }) {
  return (
    <div className="card">
      <div className="flex" style={{ gap: 8, marginBottom: 14 }}>
        <Icon name={icon} size={17} color={color} /><b style={{ fontSize: 15 }}>{title}</b>
      </div>
      {rows.length === 0 ? <div className="empty">{empty}</div> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>{rows}</div>
      )}
    </div>
  );
}

function ProcurementDashboard({ data, user }) {
  return (
    <div>
      <h1 className="page-title">داشبورد بازرگانی</h1>
      <div className="page-sub" style={{ marginBottom: 18 }}>خرید، تأمین و بدهی به تأمین‌کنندگان</div>
      <div className="kpis" style={{ marginBottom: 16 }}>
        <Kpi variant="brand" icon="cart" iconBg="#ffffff22" iconColor="#fff" label="خرید ثبت‌شدهٔ من" value={toman(data.my_purchases)} />
        <Kpi icon="alert" iconBg="#fdeee0" iconColor="#e0912f" label="درخواست‌های خرید باز" value={data.open_requests} trend={data.open_requests ? "نیازمند اقدام" : null} />
        <Kpi icon="proforma" iconBg="#eaf0ff" iconColor="#2f6bff" label="خریدهای منتظر ثبت" value={data.pending_purchases} />
        <Kpi variant="dark" icon="pay" iconBg="#ffffff1f" iconColor="#ef8f88" label="بدهی به تأمین‌کنندگان" value={toman(data.payable)} />
      </div>
      <ListCard icon="cart" color="#e0912f" title="تأمین‌کنندگان برتر" empty="هنوز خریدی ثبت نشده."
        rows={(data.top_suppliers || []).map((s) => (
          <div className="flex" key={s.party_id} style={{ gap: 11 }}>
            <Avatar name={s.party_name} size={36} radius={11} />
            <div style={{ flex: 1, fontSize: 13.5, fontWeight: 600 }}>{s.party_name}</div>
            <div className="num" style={{ fontWeight: 700, fontSize: 13 }}>{toman(s.amount)}</div>
          </div>
        ))} />
    </div>
  );
}

function TechnicalDashboard({ data, user }) {
  return (
    <div>
      <h1 className="page-title">داشبورد فنی و پشتیبانی</h1>
      <div className="page-sub" style={{ marginBottom: 18 }}>خدمات، پشتیبانی ماهانه و یادآوری سررسیدها</div>
      <div className="kpis" style={{ marginBottom: 16 }}>
        <Kpi variant="brand" icon="trend" iconBg="#ffffff22" iconColor="#fff" label="درآمد خدمات/پشتیبانی من" value={toman(data.my_income)} />
        <Kpi icon="invoice" iconBg="#e5f6ee" iconColor="#10a86b" label="فاکتور خدمات" value={data.service_count} />
        <Kpi icon="bell" iconBg="#eaf0ff" iconColor="#2f6bff" label="فاکتور پشتیبانی ماهانه" value={data.support_count} />
        <Kpi icon="calendar" iconBg="#fdeee0" iconColor="#e0912f" label="سررسیدهای نزدیک" value={(data.support_due || []).length} />
      </div>
      <ListCard icon="calendar" color="#e0912f" title="پشتیبانی‌های نزدیک به سررسید" empty="سررسید نزدیکی وجود ندارد."
        rows={(data.support_due || []).map((s) => (
          <div className="flex" key={s.invoice} style={{ gap: 11 }}>
            <Avatar name={s.party_name} size={36} radius={11} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>{s.party_name}</div>
              <div className="muted" style={{ fontSize: 11.5 }}>{s.invoice}</div>
            </div>
            <span className="badge amber">{jalali(s.period_end)}</span>
          </div>
        ))} />
    </div>
  );
}

function FinancialDashboard({ data }) {
  const statuses = Object.entries(data.proforma_by_status || {}).filter(([, v]) => v > 0);
  const maxCount = Math.max(1, ...statuses.map(([, v]) => v));
  return (
    <div>
      <h1 className="page-title">داشبورد {data.role === "management" ? "مدیریت" : "حسابداری"}</h1>
      <div className="page-sub" style={{ marginBottom: 18 }}>نمای یکپارچهٔ مالی همهٔ بخش‌ها</div>
      <div className="kpis" style={{ marginBottom: 16 }}>
        <Kpi icon="coins" iconBg="#e9f0ff" iconColor="#2f6bff" label="درآمد کل" value={toman(data.income)} />
        <Kpi icon="receive" iconBg="#e9f0ff" iconColor="#2f6bff" label="مطالبات (دریافتنی)" value={toman(data.receivable)} />
        <Kpi icon="pay" iconBg="#fdeee0" iconColor="#e0912f" label="بدهی (پرداختنی)" value={toman(data.payable)} />
        <Kpi variant="dark" icon="proforma" iconBg="#ffffff1f" iconColor="#8fd7b4" label="پیش‌فاکتورهای باز" value={data.counts.open_proformas} />
      </div>

      <div className="row" style={{ alignItems: "stretch" }}>
        <div className="card" style={{ flex: 1 }}>
          <b style={{ fontSize: 15 }}>وضعیت پیش‌فاکتورها</b>
          <div style={{ display: "flex", flexDirection: "column", gap: 13, marginTop: 16 }}>
            {statuses.length === 0 ? <div className="empty">هنوز پیش‌فاکتوری نیست.</div> : statuses.map(([k, v]) => (
              <div key={k}>
                <div className="flex" style={{ justifyContent: "space-between", fontSize: 13, marginBottom: 5 }}>
                  <span className="muted">{STATUS_FA[k] || k}</span><span className="num" style={{ fontWeight: 600 }}>{v}</span>
                </div>
                <div style={{ height: 7, background: "#eef1f7", borderRadius: 99 }}>
                  <div style={{ width: `${(v / maxCount) * 100}%`, height: 7, background: STATUS_COLOR[k], borderRadius: 99 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="card" style={{ flex: 1 }}>
          <b style={{ fontSize: 15 }}>شمارش‌ها</b>
          <table style={{ marginTop: 10 }}>
            <tbody>
              <tr><td className="muted" style={{ border: "none" }}>پیش‌فاکتورها</td><td className="num" style={{ border: "none", fontWeight: 600 }}>{data.counts.proformas}</td></tr>
              <tr><td className="muted">فاکتورها</td><td className="num" style={{ fontWeight: 600 }}>{data.counts.invoices}</td></tr>
              <tr><td className="muted">خریدها</td><td className="num" style={{ fontWeight: 600 }}>{data.counts.purchases}</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
