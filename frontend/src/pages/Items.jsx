import { useState } from "react";
import { api } from "../api";
import { Modal, useList } from "../components.jsx";

export default function Items() {
  const { data, loading, error, reload, setError } = useList("/items");
  const [editing, setEditing] = useState(null); // item object, {} for new, or null

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title">کالا و خدمات</h1>
        <button className="btn primary" onClick={() => setEditing({})}>+ مورد جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        {loading ? <div className="empty">در حال بارگذاری…</div> : (
          <table>
            <thead><tr><th>نام</th><th>نوع</th><th>واحد</th><th>کد (SKU)</th><th></th></tr></thead>
            <tbody>
              {data.map((it) => (
                <tr key={it.id}>
                  <td>{it.name}</td>
                  <td><span className={`badge ${it.kind === "GOODS" ? "blue" : "green"}`}>{it.kind_display}</span></td>
                  <td>{it.unit}</td>
                  <td dir="ltr" style={{ textAlign: "right" }}>{it.sku || "—"}</td>
                  <td style={{ textAlign: "left" }}>
                    <button className="btn sm" onClick={() => setEditing(it)}>ویرایش</button>
                  </td>
                </tr>
              ))}
              {data.length === 0 && <tr><td colSpan={5} className="empty">هنوز کالا/خدمتی ثبت نشده.</td></tr>}
            </tbody>
          </table>
        )}
      </div>

      {editing && (
        <ItemModal
          item={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); reload(); }}
          onError={setError}
        />
      )}
    </div>
  );
}

function ItemModal({ item, onClose, onSaved, onError }) {
  const isNew = !item.id;
  const [form, setForm] = useState({
    name: item.name || "", sku: item.sku || "",
    unit: item.unit || "عدد", kind: item.kind || "GOODS",
  });
  const [error, setError] = useState(null);

  async function save(e) {
    e.preventDefault();
    try {
      if (isNew) await api.post("/items", form);
      else await api.patch(`/items/${item.id}`, form);
      onSaved();
    } catch (err) {
      setError(err.message);
      onError && onError(err.message);
    }
  }

  return (
    <Modal title={isNew ? "کالا/خدمت جدید" : "ویرایش کالا/خدمت"} onClose={onClose}>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}
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
        <button className="btn primary">{isNew ? "ذخیره" : "ذخیرهٔ تغییرات"}</button>
      </form>
    </Modal>
  );
}
