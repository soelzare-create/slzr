import { useState } from "react";
import { api } from "../api";
import { Modal, useList } from "../components.jsx";
import { Avatar, Icon } from "../ui.jsx";

export default function Items() {
  const { data, loading, error, reload, setError } = useList("/items");
  const [editing, setEditing] = useState(null); // item object, {} for new, or null

  return (
    <div>
      <div className="toolbar">
        <div>
          <h1 className="page-title">کالا و خدمات</h1>
          <div className="page-sub">{data.length} مورد</div>
        </div>
        <button className="btn primary" onClick={() => setEditing({})}>+ مورد جدید</button>
      </div>
      {error && <div className="error">{error}</div>}
      {loading ? <div className="empty">در حال بارگذاری…</div> : (
        <div className="cards-grid">
          {data.map((it) => (
            <div className="pcard" key={it.id}>
              <div className="flex" style={{ alignItems: "flex-start", gap: 12 }}>
                <Avatar name={it.name} size={46} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{it.name}</div>
                  <span className={`badge ${it.kind === "GOODS" ? "blue" : "green"}`} style={{ marginTop: 4, display: "inline-block" }}>{it.kind_display}</span>
                </div>
                <button className="dot-btn" onClick={() => setEditing(it)} title="ویرایش"><Icon name="edit" size={16} /></button>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, margin: "13px 0 0" }}>
                <div className="metaline"><Icon name="card" size={14} />واحد: {it.unit}</div>
                <div className="metaline"><Icon name="doc" size={14} />کد: <span dir="ltr">{it.sku || "—"}</span></div>
              </div>
            </div>
          ))}
          {data.length === 0 && <div className="empty">هنوز کالا/خدمتی ثبت نشده.</div>}
        </div>
      )}

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
