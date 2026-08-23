import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api";
import { useTheme } from "../components/Layout";

export default function Login() {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  useTheme(); // keep the chosen theme applied on the login screen too

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const { access_token } = await api.login(phone, password);
      setToken(access_token);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-hero">
        <div className="mark">
          <div className="box">
            <img src="/logo-x.jpeg" alt="Daran X" />
          </div>
          <span>داران ایکس</span>
        </div>
        <div>
          <div className="eyebrow">DARAN X · SLZR</div>
          <h1>همه چیز سر جای خودش.</h1>
          <p>
            سامانه یکپارچه حسابداری، انبار و دفتر خرید و فروش. طراحی مقدم بر
            اجراست — پس هر عدد، هر سند و هر کالا جای مشخص خودش را دارد.
          </p>
        </div>
        <div className="steps">
          <span>شناخت</span>
          <span>طراحی</span>
          <span>اجرا</span>
          <span>پشتیبانی</span>
        </div>
      </div>

      <div className="login-side">
        <form className="login-card" onSubmit={onSubmit}>
          <h2>ورود به سامانه</h2>
          <p className="sub">با شماره تماس سازمانی خود وارد شوید.</p>

          <label>شماره تماس</label>
          <input
            className="num"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="09120000000"
            autoComplete="username"
          />

          <label style={{ marginTop: 16 }}>رمز عبور</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />

          {error && <div className="error">{error}</div>}

          <button
            type="submit"
            className="block"
            style={{ marginTop: 24 }}
            disabled={busy}
          >
            {busy ? "در حال ورود…" : "ورود"}
          </button>

          <div className="meta">
            <span>نسخه ۱٫۰</span>
            <span>پشتیبانی: ۰۲۱-۹۱۰۰۰۰۰۰</span>
          </div>
        </form>
      </div>
    </div>
  );
}
