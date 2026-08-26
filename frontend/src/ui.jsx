import { useEffect, useRef, useState } from "react";
import { toJalaali, toGregorian, jalaaliMonthLength } from "jalaali-js";
import { jalali } from "./api";

// --- Icons (inline SVG, stroke-based, no emoji) ---------------------------
const PATHS = {
  dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9"/>',
  proforma: '<path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z"/>',
  cart: '<circle cx="8" cy="21" r="1"/><circle cx="18" cy="21" r="1"/><path d="M2 3h2l2.4 12.4a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.6L23 6H5"/>',
  invoice: '<path d="M4 2h11l5 5v15l-3-2-3 2-3-2-3 2-3-2V2Z"/><path d="M8 7h6M8 11h8"/>',
  chart: '<path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="7"/><rect x="12" y="6" width="3" height="11"/><rect x="17" y="13" width="3" height="4"/>',
  doc: '<path d="M4 2h11l5 5v15H4z"/><path d="M8 7h4M8 11h8M8 15h8"/>',
  bell: '<path d="M17 8a5 5 0 0 0-10 0c0 7-2 8-2 8h14s-2-1-2-8"/><path d="M10.3 20a1.9 1.9 0 0 0 3.4 0"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  dots: '<circle cx="12" cy="5" r="1.6" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/><circle cx="12" cy="19" r="1.6" fill="currentColor" stroke="none"/>',
  phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.6A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.6a16 16 0 0 0 6 6l1.1-1.1a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2Z"/>',
  pin: '<path d="M20 10c0 6-8 11-8 11s-8-5-8-11a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  alert: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/>',
  ledger: '<path d="M3 3v18h18"/><path d="M7 15l3-3 3 2 4-5"/>',
  receive: '<path d="M12 5v14M5 12l7 7 7-7"/>',
  pay: '<path d="M12 19V5M5 12l7-7 7 7"/>',
  card: '<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="12" cy="12" r="3"/>',
  edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  chevron: '<path d="M6 9l6 6 6-6"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/>',
  trend: '<path d="M3 17l6-6 4 4 8-8"/><path d="M17 7h4v4"/>',
  coins: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
  target: '<path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/><path d="M22 4 12 14.01l-3-3"/>',
};

export function Icon({ name, size = 18, color = "currentColor", fill = "none", strokeWidth = 2 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke={color}
      strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"
      dangerouslySetInnerHTML={{ __html: PATHS[name] || "" }} />
  );
}

// --- Avatar ----------------------------------------------------------------
const GRADS = [
  "linear-gradient(135deg,#2f6bff,#5b4be6)",
  "linear-gradient(135deg,#10a86b,#0c8f5b)",
  "linear-gradient(135deg,#e0912f,#c9761a)",
  "linear-gradient(135deg,#8b5cf6,#6d28d9)",
  "linear-gradient(135deg,#0ea5b7,#0b8494)",
  "linear-gradient(135deg,#ef6461,#d43f3c)",
  "linear-gradient(135deg,#334155,#1e293b)",
];

export function initials(name = "") {
  const parts = String(name).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "؟";
  if (parts.length === 1) return parts[0].slice(0, 2);
  return parts[0][0] + "." + parts[1][0];
}

function hashIndex(str, mod) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h % mod;
}

export function Avatar({ name, size = 44, radius = 14, fontSize }) {
  return (
    <div className="avatar" style={{
      width: size, height: size, borderRadius: radius,
      background: GRADS[hashIndex(name || "", GRADS.length)],
      fontSize: fontSize || Math.round(size * 0.34),
    }}>{initials(name)}</div>
  );
}

// --- Dropdown menu (3-dot) -------------------------------------------------
export function Menu({ items, title }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    function onDoc(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);
  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button className={`dot-btn ${open ? "open" : ""}`} onClick={() => setOpen(!open)} aria-label="اقدامات">
        <Icon name="dots" />
      </button>
      {open && (
        <div className="menu">
          {title && <div className="head">{title}</div>}
          {items.map((it, i) => it.sep ? <div key={i} className="sep" /> : (
            <button key={i} onClick={() => { setOpen(false); it.onClick && it.onClick(); }}>
              {it.icon && <Icon name={it.icon} size={16} color={it.color || "#4a5468"} />}
              {it.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Jalali (Shamsi) date picker ------------------------------------------
const J_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
  "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
const J_WEEK = ["ش", "ی", "د", "س", "چ", "پ", "ج"];
const fa = (n) => Number(n).toLocaleString("fa-IR", { useGrouping: false });
const pad = (n) => String(n).padStart(2, "0");

function isoToJalali(iso) {
  if (!iso) return null;
  const [y, m, d] = iso.split("-").map(Number);
  return toJalaali(y, m, d);
}

export function JalaliDatePicker({ value, onChange, placeholder = "انتخاب تاریخ" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const todayJ = toJalaali(new Date());
  const sel = isoToJalali(value);
  const [view, setView] = useState(sel ? { jy: sel.jy, jm: sel.jm } : { jy: todayJ.jy, jm: todayJ.jm });

  useEffect(() => {
    function onDoc(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  function pick(jd) {
    const g = toGregorian(view.jy, view.jm, jd);
    onChange(`${g.gy}-${pad(g.gm)}-${pad(g.gd)}`);
    setOpen(false);
  }
  function shift(delta) {
    let { jy, jm } = view;
    jm += delta;
    if (jm < 1) { jm = 12; jy--; } else if (jm > 12) { jm = 1; jy++; }
    setView({ jy, jm });
  }

  const first = toGregorian(view.jy, view.jm, 1);
  const offset = (new Date(first.gy, first.gm - 1, first.gd).getDay() + 1) % 7;
  const len = jalaaliMonthLength(view.jy, view.jm);
  const cells = [...Array(offset).fill(null), ...Array.from({ length: len }, (_, i) => i + 1)];

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <div onClick={() => setOpen(!open)} style={{
        border: "1px solid #e3e7f0", borderRadius: 10, padding: "10px 12px", background: "#fafbfe",
        fontSize: 14, display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer",
      }}>
        <span style={{ color: value ? "#10151f" : "#9aa3b5" }}>{value ? jalali(value) : placeholder}</span>
        <Icon name="calendar" size={15} color="#b6becb" />
      </div>
      {open && (
        <div style={{
          position: "absolute", bottom: 48, right: 0, width: 258, background: "#fff",
          border: "1px solid var(--line)", borderRadius: 14, boxShadow: "var(--shadow-pop)",
          padding: 12, zIndex: 40,
        }}>
          <div className="flex" style={{ justifyContent: "space-between", marginBottom: 10 }}>
            <button type="button" className="dot-btn" onClick={() => shift(-1)}><Icon name="chevron" size={16} /></button>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{J_MONTHS[view.jm - 1]} {fa(view.jy)}</div>
            <button type="button" className="dot-btn" onClick={() => shift(1)} style={{ transform: "rotate(180deg)" }}><Icon name="chevron" size={16} /></button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 2, textAlign: "center" }}>
            {J_WEEK.map((w) => <div key={w} style={{ fontSize: 11, color: "var(--muted-2)", padding: "4px 0" }}>{w}</div>)}
            {cells.map((jd, i) => jd === null ? <div key={i} /> : (
              <button type="button" key={i} onClick={() => pick(jd)} style={{
                border: "none", borderRadius: 8, padding: "7px 0", fontSize: 12.5, fontFamily: "inherit",
                background: sel && sel.jy === view.jy && sel.jm === view.jm && sel.jd === jd ? "var(--brand)" : "transparent",
                color: sel && sel.jy === view.jy && sel.jm === view.jm && sel.jd === jd ? "#fff" : "#10151f",
                outline: todayJ.jy === view.jy && todayJ.jm === view.jm && todayJ.jd === jd ? "1px solid #cdd9f5" : "none",
              }}>{fa(jd)}</button>
            ))}
          </div>
          <button type="button" onClick={() => { const t = toJalaali(new Date()); setView({ jy: t.jy, jm: t.jm }); pick(t.jd); }}
            style={{ marginTop: 10, width: "100%", border: "1px solid var(--line)", borderRadius: 9, padding: "7px", background: "#f6f8fc", fontSize: 12.5, fontFamily: "inherit" }}>امروز</button>
        </div>
      )}
    </div>
  );
}

export function Modal({ title, icon, onClose, children, wide }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className={`modal ${wide ? "wide" : ""}`} onClick={(e) => e.stopPropagation()}>
        <div className="m-head">
          <div className="flex">
            {icon && <div style={{ width: 38, height: 38, borderRadius: 11, background: "#eaf0ff", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon name={icon} size={19} color="#2f6bff" /></div>}
            <h2>{title}</h2>
          </div>
          <button className="modal-close" onClick={onClose}><Icon name="close" size={16} /></button>
        </div>
        <div className="m-body">{children}</div>
      </div>
    </div>
  );
}
