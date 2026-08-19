import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { setToken } from "../api";
import { ROLE_FA, ACCOUNTING_ROLES } from "../labels";

export default function Layout({ me, children }) {
  const navigate = useNavigate();

  function logout() {
    setToken(null);
    navigate("/login");
  }

  const link = ({ isActive }) => ({
    color: "#fff",
    textDecoration: "none",
    padding: "6px 10px",
    borderRadius: 8,
    background: isActive ? "rgba(255,255,255,0.18)" : "transparent",
  });

  return (
    <div>
      <header className="app-header">
        <div className="row" style={{ gap: 18 }}>
          <div>
            <div className="brand">داران‌ایکس</div>
            <div className="motto">همه چیز سر جای خودش</div>
          </div>
          <nav className="row" style={{ gap: 4 }}>
            <NavLink to="/" end style={link}>
              داشبورد
            </NavLink>
            <NavLink to="/customers" style={link}>
              مشتری‌ها
            </NavLink>
            <NavLink to="/suppliers" style={link}>
              تأمین‌کننده‌ها
            </NavLink>
            <NavLink to="/activities" style={link}>
              فعالیت‌ها
            </NavLink>
            <NavLink to="/inventory" style={link}>
              انبار
            </NavLink>
            <NavLink to="/purchases" style={link}>
              خریدها
            </NavLink>
            <NavLink to="/support" style={link}>
              پشتیبانی
            </NavLink>
            {me && ACCOUNTING_ROLES.includes(me.role) && (
              <NavLink to="/accounting" style={link}>
                حسابداری
              </NavLink>
            )}
          </nav>
        </div>
        <div className="row">
          {me && (
            <span>
              {me.name}{" "}
              <span className="badge">{ROLE_FA[me.role] || me.role}</span>
            </span>
          )}
          <button
            className="secondary"
            style={{ width: "auto", marginTop: 0 }}
            onClick={logout}
          >
            خروج
          </button>
        </div>
      </header>
      <div className="container">{children}</div>
    </div>
  );
}
