import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "./auth.jsx";
import { api } from "./api";
import { Avatar, Icon } from "./ui.jsx";

const NAV = [
  { to: "/", label: "داشبورد", icon: "dashboard", perm: null },
  { to: "/parties", label: "مشتری‌ها", icon: "users", perm: null },
  { to: "/proformas", label: "پیش‌فاکتورها", icon: "proforma", perm: "sales.view" },
  { to: "/purchases", label: "خریدها", icon: "cart", perm: "procurement.view" },
  { to: "/invoices", label: "فاکتورها", icon: "invoice", perm: "sales.view" },
  { to: "/accounting", label: "حسابداری", icon: "chart", perm: "accounting.view" },
  { to: "/items", label: "کالا و خدمات", icon: "doc", perm: null },
  { to: "/notifications", label: "اعلان‌ها", icon: "bell", perm: null },
  { to: "/users", label: "حساب‌های کاربری", icon: "users", perm: null, adminOnly: true },
];

const ROLE_LABEL = {
  sales: "بخش فروش", accounting: "بخش حسابداری", procurement: "بخش بازرگانی",
  technical: "بخش فنی", management: "مدیریت",
};

export default function Layout({ children }) {
  const { user, logout, can } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    api.get("/notifications/unread_count").then((d) => setUnread(d.count)).catch(() => {});
  }, []);

  const items = NAV.filter((n) => (!n.perm || can(n.perm)) && (!n.adminOnly || user?.is_system_admin));
  const dept = (user?.department_codes || [])[0];
  const roleLabel = user?.is_system_admin ? "ادمین سیستم" : (ROLE_LABEL[dept] || "کاربر");

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo"><Icon name="chart" size={20} color="#fff" strokeWidth={2.2} /></div>
          <div><div className="title">داران ایکس</div><div className="sub">همه چیز سر جای خودش</div></div>
        </div>
        <nav className="nav">
          {items.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === "/"}>
              <Icon name={n.icon} />
              <span>{n.label}</span>
              {n.to === "/notifications" && unread > 0 && <span className="count">{unread}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="side-user">
          <Avatar name={user?.full_name} size={36} radius={11} />
          <div style={{ minWidth: 0 }}>
            <div className="name">{user?.full_name}</div>
            <div className="role">{roleLabel}</div>
          </div>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="search">
            <Icon name="search" size={16} color="#8b95a8" />
            <input placeholder="جستجو…" />
          </div>
          <div className="flex" style={{ gap: 14 }}>
            <button className="btn icon" style={{ position: "relative" }} onClick={logout} title="خروج">
              <Icon name="logout" size={18} color="#4a5468" />
            </button>
            <Avatar name={user?.full_name} size={38} radius={11} />
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
