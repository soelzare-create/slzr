import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, rows, toman } from "../api";
import { useAuth } from "../auth.jsx";
import { Avatar, Icon, Menu, Modal } from "../ui.jsx";

const SETTLE = {
  settled: { cls: "green", label: "تسویه‌شده", icon: "check" },
  debtor: { cls: "red", label: "بدهکار", icon: "alert" },
  creditor: { cls: "amber", label: "طلبکار از ما", icon: "alert" },
};

export default function Parties() {
  const navigate = useNavigate();
  const { can } = useAuth();
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [editing, setEditing] = useState(null); // party object or {} for new

  function reload() {
    setLoading(true);
    api.get("/parties/cards")
      .then((d) => setCards(rows(d)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { reload(); }, []);

  const shown = cards.filter((c) => {
    if (filter === "customer") return c.is_customer;
    if (filter === "supplier") return c.is_supplier;
    if (filter === "debtor") return c.settle_status === "debtor";
    return true;
  });

  function menuFor(c) {
    const items = [];
    if (c.is_customer) {
      items.push({ label: "ثبت پیش‌فاکتور", icon: "proforma", color: "#2f6bff",
        onClick: () => navigate(`/proformas?customer=${c.id}`) });
      items.push({ label: "فاکتور خدمات", icon: "invoice", color: "#2f6bff",
        onClick: () => navigate(`/invoices?customer=${c.id}`) });
    }
    if (c.is_supplier) {
      items.push({ label: "ثبت خرید", icon: "cart", color: "#e0912f",
        onClick: () => navigate(`/purchases?supplier=${c.id}`) });
    }
    if (can("accounting.edit")) {
      if (c.is_customer) items.push({ label: "دریافت وجه", icon: "receive", color: "#10a86b",
        onClick: () => navigate(`/accounting?doc=receipt&party=${c.id}`) });
      if (c.is_supplier) items.push({ label: "پرداخت وجه", icon: "pay", color: "#e0483d",
        onClick: () => navigate(`/accounting?doc=payment&party=${c.id}`) });
    }
    items.push({ label: "کارنامهٔ مالی", icon: "ledger", onClick: () => navigate("/accounting") });
    items.push({ sep: true });
    items.push({ label: "ویرایش اطلاعات", icon: "edit", onClick: () => setEditing(c) });
    return items;
  }

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">مشتری‌ها و طرف‌حساب‌ها</h1>
          <div className="page-sub">{cards.length} طرف‌حساب — فرآیندها از اینجا آغاز می‌شوند</div>
        </div>
        <div className="flex">
          <div className="seg" style={{ background: "#eef1f7" }}>
            {[["all", "همه"], ["customer", "مشتری"], ["supplier", "تأمین‌کننده"], ["debtor", "بدهکار"]].map(([k, l]) => (
              <button key={k} className={filter === k ? "active" : ""} onClick={() => setFilter(k)}>{l}</button>
            ))}
          </div>
          <button className="btn primary icon" onClick={() => setEditing({})} title="مشتری جدید"><Icon name="plus" strokeWidth={2.3} /></button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {loading ? <div className="empty">در حال بارگذاری…</div> : (
        <div className="cards-grid">
          {shown.map((c) => {
            const s = SETTLE[c.settle_status] || SETTLE.settled;
            const isSupplierOnly = c.is_supplier && !c.is_customer;
            return (
              <div className="pcard" key={c.id}>
                <div className="flex" style={{ alignItems: "flex-start", gap: 12 }}>
                  <Avatar name={c.name} size={46} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 15 }}>{c.name}</div>
                    <div className="flex" style={{ gap: 5, marginTop: 3 }}>
                      {c.is_customer && <span className="badge blue">مشتری</span>}
                      {c.is_supplier && <span className="badge amber">تأمین‌کننده</span>}
                    </div>
                  </div>
                  <Menu title="اقدامات با این طرف‌حساب" items={menuFor(c)} />
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6, margin: "13px 0 0" }}>
                  <div className="metaline"><Icon name="phone" size={14} /><span dir="ltr">{c.phone || "—"}</span></div>
                  <div className="metaline"><Icon name="pin" size={14} />{(c.address || "—").split("،")[0] || "—"}</div>
                </div>
                <div className="foot">
                  <div>
                    <div style={{ fontSize: 11, color: "var(--muted-2)" }}>{isSupplierOnly ? "خرید از این تأمین‌کننده" : "فروش کل"}</div>
                    <div className="num" style={{ fontWeight: 700, fontSize: 14 }}>{toman(c.sales_total)}</div>
                  </div>
                  <span className={`badge ${s.cls}`}><Icon name={s.icon} size={12} strokeWidth={2.5} />{s.label}{c.balance ? ` ${toman(Math.abs(c.balance))}` : ""}</span>
                </div>
              </div>
            );
          })}
          <button className="pcard" onClick={() => setEditing({})} style={{ borderStyle: "dashed", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8, color: "var(--muted)", minHeight: 170, cursor: "pointer" }}>
            <div style={{ width: 44, height: 44, borderRadius: 14, background: "#f1f3f9", display: "flex", alignItems: "center", justifyContent: "center" }}><Icon name="plus" size={20} color="#9aa3b5" /></div>
            <div style={{ fontSize: 13 }}>افزودن طرف‌حساب جدید</div>
          </button>
        </div>
      )}

      {editing && <PartyModal party={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); reload(); }} />}
    </div>
  );
}

function PartyModal({ party, onClose, onSaved }) {
  const isNew = !party.id;
  const [form, setForm] = useState({
    name: party.name || "", phone: party.phone || "", address: party.address || "",
    is_customer: party.is_customer ?? true, is_supplier: party.is_supplier ?? false,
    national_id: party.national_id || "",
  });
  const [error, setError] = useState(null);

  async function save(e) {
    e.preventDefault();
    try {
      if (isNew) await api.post("/parties", form);
      else await api.patch(`/parties/${party.id}`, form);
      onSaved();
    } catch (err) { setError(err.message); }
  }

  return (
    <Modal title={isNew ? "طرف‌حساب جدید" : "ویرایش طرف‌حساب"} icon="users" onClose={onClose}>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>نام</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div className="row">
          <div className="field"><label>تلفن</label><input dir="ltr" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
          <div className="field"><label>کد ملی/اقتصادی</label><input value={form.national_id} onChange={(e) => setForm({ ...form, national_id: e.target.value })} /></div>
        </div>
        <div className="field"><label>آدرس</label><textarea rows={2} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></div>
        <div className="row" style={{ marginBottom: 18 }}>
          <label className="flex" style={{ fontSize: 14 }}><input type="checkbox" style={{ width: "auto" }} checked={form.is_customer} onChange={(e) => setForm({ ...form, is_customer: e.target.checked })} /> مشتری</label>
          <label className="flex" style={{ fontSize: 14 }}><input type="checkbox" style={{ width: "auto" }} checked={form.is_supplier} onChange={(e) => setForm({ ...form, is_supplier: e.target.checked })} /> تأمین‌کننده</label>
        </div>
        <button className="btn primary" style={{ width: "100%" }}>{isNew ? "افزودن طرف‌حساب" : "ذخیرهٔ تغییرات"}</button>
      </form>
    </Modal>
  );
}
