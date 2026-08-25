import { useState } from "react";
import { api } from "../api";
import { Modal, useList } from "../components.jsx";

export default function Items() {
  const { data, loading, error, reload, setError } = useList("/items");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(blank());

  function blank() {
    return { name: "", sku: "", unit: "عدد", kind: "GOODS" };
  }

  async function save(e) {
    e.preventDefault();
    try {
      await api.post("/items", form);
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
        <h1 className="page-title">کالا و خدمات</h1>
        <button className="btn primary" onClick={() => setOpen(true)}>+ مورد جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>نام</th><th>نوع</th><th>واحد</th><th>کد (SKU)</th></tr></thead>
            <tbody>
              {data.map((it) => (
                <tr key={it.id}>
                  <td>{it.name}</td>
                  <td><span className={`badge ${it.kind === "GOODS" ? "blue" : "green"}`}>{it.kind_display}</span></td>
                  <td>{it.unit}</td>
                  <td dir="ltr" style={{ textAlign: "right" }}>{it.sku || "—"}</td>
                </tr>
              ))}
              {data.length === 0 && <tr><td colSpan={4} className="empty">هنوز کالا/خدمتی ثبت نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {open && (
        <Modal title="کالا/خدمت جدید" onClose={() => setOpen(false)}>
          <form onSubmit={save}>
            <div className="field">
              <label>نام</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="row">
              <div className="field">
                <label>نوع</label>
                <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
                  <option value="GOODS">کالا</option>
                  <option value="SERVICE">خدمت</option>
                </select>
              </div>
              <div className="field">
                <label>واحد</label>
                <input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
              </div>
              <div className="field">
                <label>کد (SKU)</label>
                <input dir="ltr" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} />
              </div>
            </div>
            <button className="btn primary">ذخیره</button>
          </form>
        </Modal>
      )}
    </div>
  );
}
