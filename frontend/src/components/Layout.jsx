import React, { useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { setToken } from "../api";
import { ROLE_FA, ACCOUNTING_ROLES } from "../labels";

// Screen titles for the sticky header, keyed by route.
const SCREENS = {
  "/": ["داشبورد", "نمای کلی مالی و عملیاتی سازمان"],
  "/activities": ["فعالیت‌ها", "پروژه، فروش کالا و قرارداد پشتیبانی"],
  "/proformas": ["پیش‌فاکتورها", "پیشنهاد قیمت پیش از صدور فاکتور نهایی"],
  "/invoices": ["فاکتورها", "فاکتور نهایی؛ ثبت درآمد و کسر موجودی"],
  "/customers": ["مشتری‌ها", "طرف‌حساب‌های فروش و افراد رابط آن‌ها"],
  "/suppliers": ["تأمین‌کننده‌ها", "طرف‌حساب‌های خرید و افراد رابط آن‌ها"],
  "/inventory": ["انبار", "مدل‌های کالا، سریال‌ها و حرکت‌های انبار"],
  "/purchases": ["خریدها", "اسناد خرید از تأمین‌کننده و ورود کالا"],
  "/accounting": ["حسابداری", "اسناد مالی، صندوق و بانک، چک و اقساط"],
  "/referrals": ["ارجاعات", "کارهای ارجاع‌شده بین اعضای تیم"],
};

const THEME_KEY = "daranx_theme";

export function useTheme() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem(THEME_KEY) || "light"
  );
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);
  return [theme, setTheme];
}

const initials = (name) =>
  (name || "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join("‌");

export default function Layout({ me, title, subtitle, actions, children }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [theme, setTheme] = useTheme();

  const [fallbackTitle, fallbackSubtitle] = SCREENS[pathname] || ["داران ایکس", ""];

  function logout() {
    setToken(null);
    navigate("/login");
  }

  const groups = [
    { title: "نمای کلی", items: [["/", "داشبورد"]] },
    {
      title: "فروش",
      items: [
        ["/activities", "فعالیت‌ها"],
        ["/proformas", "پیش‌فاکتورها"],
        ["/invoices", "فاکتورها"],
      ],
    },
    {
      title: "طرف‌حساب",
      items: [
        ["/customers", "مشتری‌ها"],
        ["/suppliers", "تأمین‌کننده‌ها"],
      ],
    },
    {
      title: "انبار و خرید",
      items: [
        ["/inventory", "انبار"],
        ["/purchases", "خریدها"],
      ],
    },
    {
      title: "مالی و تیم",
      items: [
        ...(me && ACCOUNTING_ROLES.includes(me.role)
          ? [["/accounting", "حسابداری"]]
          : []),
        ["/referrals", "ارجاعات"],
      ],
    },
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="logo">
            <img src="/logo-x.jpeg" alt="Daran X" />
          </div>
          <div>
            <div className="brand">داران ایکس</div>
            <div className="motto">همه چیز سر جای خودش</div>
          </div>
        </div>
        <div className="rule" />
        <nav>
          {groups.map((g) => (
            <div className="nav-group" key={g.title}>
              <div className="nav-title">{g.title}</div>
              {g.items.map(([to, label]) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    isActive ? "nav-link active" : "nav-link"
                  }
                >
                  <span>{label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="foot">فناوری قابل اعتماد برای رشد پایدار کسب‌وکارها</div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="titles">
            <h1>{title || fallbackTitle}</h1>
            <p>{subtitle || fallbackSubtitle}</p>
          </div>
          {actions}
          <button
            className="ghost"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? "تم روشن" : "تم تیره"}
          </button>
          {me && (
            <div className="user-chip">
              <div style={{ textAlign: "left" }}>
                <div className="name">{me.name}</div>
                <div className="role">{ROLE_FA[me.role] || me.role}</div>
              </div>
              <div className="avatar">{initials(me.name)}</div>
            </div>
          )}
          <button className="ghost" onClick={logout}>
            خروج
          </button>
        </header>
        <div className="container">{children}</div>
      </main>
    </div>
  );
}
