import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth.jsx";

// Company profile (letterhead + bank details) shown on printed documents.
// Editable by the system admin only.
const FIELDS = [
  ["name", "نام برند (لاتین)"],
  ["brand_sub", "زیرعنوان (فارسی)"],
  ["address", "آدرس", "wide"],
  ["phone1", "تلفن ۱"],
  ["phone2", "تلفن ۲"],
  ["mobile", "موبایل"],
  ["email", "پست الکترونیک"],
  ["website", "وب‌سایت"],
  ["economic_code", "کد اقتصادی شرکت"],
  ["registration_no", "شماره ثبت شرکت"],
  ["bank_name", "نام بانک"],
  ["bank_branch", "شعبه"],
  ["bank_account", "شماره حساب"],
  ["bank_iban", "شماره شبا"],
  ["bank_branch_code", "کد شعبه"],
];

export default function CompanySettings() {
  const { user } = useAuth();
  const [form, setForm] = useState(null);
  const [error, setError] = useState(null);
  const [ok, setOk] = useState(false);
  const isAdmin = !!user?.is_system_admin;

  useEffect(() => { api.get("/company").then(setForm).catch((e) => setError(e.message)); }, []);

  async function save(e) {
    e.preventDefault();
    setError(null); setOk(false);
    try { const d = await api.patch("/company", form); setForm(d); setOk(true); }
    catch (err) { setError(err.message); }
  }

  if (!form) return <div className="empty">در حال بارگذاری…</div>;

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">تنظیمات شرکت</h1>
          <div className="page-sub">اطلاعات سربرگ و حساب بانکی که روی فاکتور/پیش‌فاکتور چاپ می‌شود</div>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {ok && <div className="card" style={{ borderColor: "#10a86b", color: "#10a86b", marginBottom: 12 }}>تغییرات ذخیره شد.</div>}
      {!isAdmin && <div className="card" style={{ marginBottom: 12 }}>این اطلاعات فقط توسط ادمین سیستم قابل ویرایش است.</div>}
      <form className="card" onSubmit={save}>
        <div className="grid2" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px 20px" }}>
          {FIELDS.map(([key, label, wide]) => (
            <div className="field" key={key} style={wide ? { gridColumn: "1 / -1" } : undefined}>
              <label>{label}</label>
              <input dir={/email|website|iban|account|phone|mobile|code/.test(key) ? "ltr" : undefined}
                value={form[key] || ""} disabled={!isAdmin}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
            </div>
          ))}
        </div>
        {isAdmin && <button className="btn primary" style={{ marginTop: 14 }}>ذخیرهٔ تنظیمات</button>}
      </form>
    </div>
  );
}
