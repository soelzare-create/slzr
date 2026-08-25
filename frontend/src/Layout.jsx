import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "./auth.jsx";
import { api } from "./api";

const NAV = [
  { to: "/", label: "داشبورد", icon: "🏠", perm: null },
  { to: "/proformas", label: "پیش‌فاکتورها", icon: "📝", perm: "sales.view" },
  { to: "/purchases", label: "خریدها", icon: "🛒", perm: "procurement.view" },
  { to: "/invoices", label: "فاکتورها", icon: "🧾", perm: "sales.view" },
  { to: "/parties", label: "طرف‌حساب‌ها", icon: "👥", perm: null },
  { to: "/items", label: "کالا و خدمات", icon: "📦", perm: null },
  { to: "/accounting", label: "حسابداری", icon: "📊", perm: "accounting.view" },
  { to: "/notifications", label: "اعلان‌ها", icon: "🔔", perm: null },
];

export default function Layout({ children }) {
  const { user, logout, can } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    api.get("/notifications/unread_count").then((d) => setUnread(d.count)).catch(() => {});
  }, []);

  const items = NAV.filter((n) => !n.perm || can(n.perm));

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          داران ایکس
          <small>همه چیز سر جای خودش</small>
        </div>
        <nav className="nav">
          {items.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === "/"}>
              <span>{n.icon}</span>
              <span>{n.label}</span>
              {n.to === "/notifications" && unread > 0 && (
                <span className="badge red" style={{ marginInlineStart: "auto" }}>{unread}</span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="user">
            {user?.full_name}
            {user?.is_system_admin && <span className="badge blue" style={{ marginInlineStart: 8 }}>ادمین سیستم</span>}
          </div>
          <button className="btn sm" onClick={logout}>خروج</button>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
