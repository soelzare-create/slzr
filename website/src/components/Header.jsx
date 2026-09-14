import { useState } from "react";
import Logo from "./Logo.jsx";
import { brand, nav } from "../data.js";

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="container">
        <a className="brand-lockup" href="#top" aria-label={brand.name}>
          <Logo size={38} />
          <span className="name">{brand.name}</span>
        </a>

        <nav className={`nav ${open ? "open" : ""}`} aria-label="ناوبری اصلی">
          {nav.map((item) => (
            <a key={item.href} href={item.href} onClick={() => setOpen(false)}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="header-cta">
          <a className="btn primary" href="#contact">
            گفت‌وگو با ما
          </a>
          <button
            className="btn nav-toggle"
            aria-label="باز و بسته کردن منو"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {open ? (
                <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
              ) : (
                <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
