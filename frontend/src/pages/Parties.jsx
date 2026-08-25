import { useState } from "react";
import { api } from "../api";
import { Modal, useList } from "../components.jsx";

export default function Parties() {
  const { data, loading, error, reload, setError } = useList("/parties");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(blank());

  function blank() {
    return { name: "", is_customer: true, is_supplier: false, phone: "", national_id: "", address: "" };
  }

  async function save(e) {
    e.preventDefault();
    try {
      await api.post("/parties", form);
      setOpen(false);
      setForm(blank());
      reload();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title">طرف‌حساب‌ها</h1>
        <button className="btn primary" onClick={() => setOpen(true)}>+ طرف‌حساب جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>نام</th><th>نوع</th><th>تلفن</th><th>کد ملی/اقتصادی</th></tr></thead>
            <tbody>
              {data.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>
                    {p.is_customer && <span className="badge blue">مشتری</span>}{" "}
                    {p.is_supplier && <span className="badge amber">تأمین‌کننده</span>}
                  </td>
                  <td dir="ltr" style={{ textAlign: "right" }}>{p.phone || "—"}</td>
                  <td>{p.national_id || "—"}</td>
                </tr>
              ))}
              {data.length === 0 && <tr><td colSpan={4} className="empty">هنوز طرف‌حسابی ثبت نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {open && (
        <Modal title="طرف‌حساب جدید" onClose={() => setOpen(false)}>
          <form onSubmit={save}>
            <div className="field">
              <label>نام</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="row">
              <div className="field">
                <label>تلفن</label>
                <input dir="ltr" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
              <div className="field">
                <label>کد ملی/اقتصادی</label>
                <input value={form.national_id} onChange={(e) => setForm({ ...form, national_id: e.target.value })} />
              </div>
            </div>
            <div className="row">
              <label className="flex"><input type="checkbox" style={{ width: "auto" }} checked={form.is_customer} onChange={(e) => setForm({ ...form, is_customer: e.target.checked })} /> مشتری</label>
              <label className="flex"><input type="checkbox" style={{ width: "auto" }} checked={form.is_supplier} onChange={(e) => setForm({ ...form, is_supplier: e.target.checked })} /> تأمین‌کننده</label>
            </div>
            <div className="field">
              <label>آدرس</label>
              <textarea rows={2} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </div>
            <button className="btn primary">ذخیره</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
