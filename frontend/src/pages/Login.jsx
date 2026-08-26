import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { Icon } from "../ui.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [phone, setPhone] = useState("09120000000");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try { await login(phone, password); navigate("/"); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return (
    <div className="login-wrap">
      <div className="login-form">
        <form className="inner" onSubmit={submit}>
          <div className="flex" style={{ gap: 11, marginBottom: 34 }}>
            <div style={{ width: 44, height: 44, borderRadius: 13, background: "var(--brand-grad)", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon name="chart" size={23} color="#fff" strokeWidth={2.2} /></div>
            <div><div style={{ fontWeight: 700, fontSize: 19 }}>داران ایکس</div><div style={{ fontSize: 12, color: "var(--muted)" }}>سیستم یکپارچه حسابداری و فاکتور</div></div>
          </div>
          <div style={{ fontSize: 25, fontWeight: 700, marginBottom: 6 }}>ورود به حساب</div>
          <div style={{ fontSize: 14, color: "var(--muted)", marginBottom: 26 }}>برای ادامه، اطلاعات حساب خود را وارد کنید.</div>
          {error && <div className="error">{error}</div>}
          <div className="field">
            <label>شماره تماس</label>
            <input dir="ltr" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div className="field">
            <label>رمز عبور</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <button className="btn primary" style={{ width: "100%", height: 48, marginTop: 6, justifyContent: "center", display: "flex", alignItems: "center", gap: 8 }} disabled={busy}>
            {busy ? "در حال ورود…" : "ورود"}{!busy && <Icon name="logout" size={17} color="#fff" />}
          </button>
          <div style={{ textAlign: "center", fontSize: 12.5, color: "var(--muted-2)", marginTop: 26 }}>© داران ایکس — همه چیز سر جای خودش</div>
        </form>
      </div>
      <div className="login-side">
        <svg style={{ position: "absolute", inset: 0, opacity: .5 }} width="100%" height="100%"><defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#ffffff0d" strokeWidth="1" /></pattern></defs><rect width="100%" height="100%" fill="url(#grid)" /></svg>
        <div style={{ position: "absolute", width: 460, height: 460, borderRadius: "50%", background: "radial-gradient(circle,#2f6bff33,transparent 70%)", top: -120, left: -120 }} />
        <div style={{ position: "relative", width: 380, padding: 20 }}>
          <div className="flex" style={{ display: "inline-flex", gap: 8, background: "#ffffff14", border: "1px solid #ffffff1f", borderRadius: 999, padding: "6px 14px", fontSize: 12.5, color: "#bcd0ff", marginBottom: 24 }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#8fd7b4" }} />نسخهٔ فاز ۱ — یکپارچه و اتمیک
          </div>
          <div style={{ fontSize: 29, fontWeight: 700, lineHeight: 1.5, marginBottom: 16 }}>حسابداری و فاکتور،<br />همه در یک جا.</div>
          <div style={{ fontSize: 14.5, color: "#9fb0d0", lineHeight: 2 }}>اسناد مالی به‌صورت خودکار از خرید و فروش تولید می‌شوند. قانون ۵٪، رزرو نرم و دفتر کل — همه یکپارچه.</div>
        </div>
      </div>
    </div>
  );
}
