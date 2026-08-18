import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

const ROLE_FA = {
  manager: "مدیر",
  sales: "فروش",
  technical: "فنی",
  warehouse: "انباردار",
  accountant: "حسابدار",
};

export default function Dashboard() {
  const [me, setMe] = useState(null);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  function logout() {
    setToken(null);
    navigate("/login");
  }

  useEffect(() => {
    api
      .me()
      .then((u) => {
        setMe(u);
        // Only managers may list users (RBAC enforced by the API too).
        if (u.role === "manager") {
          api.listUsers().then(setUsers).catch((e) => setError(e.message));
        }
      })
      .catch(() => logout());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <div>
      <header className="app-header">
        <div>
          <div className="brand">داران‌ایکس</div>
          <div className="motto">همه چیز سر جای خودش</div>
        </div>
        <div className="row">
          <span>
            {me.name} <span className="badge">{ROLE_FA[me.role] || me.role}</span>
          </span>
          <button
            className="secondary"
            style={{ width: "auto", marginTop: 0 }}
            onClick={logout}
          >
            خروج
          </button>
        </div>
      </header>

      <div className="container">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>خوش آمدید</h2>
          <p>
            این داشبورد فاز ۱ (پایه) است: احراز هویت، کاربران و نقش‌ها. بخش‌های
            بعدی (مشتری، فعالیت، انبار، فاکتور، حسابداری، پشتیبانی) در فازهای بعد
            اضافه می‌شوند.
          </p>
        </div>

        {me.role === "manager" && (
          <div className="card" style={{ marginTop: 20 }}>
            <h2 style={{ marginTop: 0 }}>کاربران تیم</h2>
            {error && <div className="error">{error}</div>}
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
      </div>
    </div>
  );
}
