import React, { useEffect, useState } from "react";
import { api } from "../api";
import { INVOICE_KIND_FA, INVOICE_STATUS_FA } from "../labels";

// Items + invoices (proforma/final) for one activity. Sales/manager can write.
export default function SalesPanel({ activityId, canWrite, onChanged }) {
  const [items, setItems] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [models, setModels] = useState([]);
  const [error, setError] = useState("");

  // add-item form
  const [modelId, setModelId] = useState("");
  const [units, setUnits] = useState([]); // in-stock serial units for the chosen model
  const [stockItemId, setStockItemId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");

  // invoice form
  const [dueDate, setDueDate] = useState("");

  const selectedModel = models.find((m) => String(m.id) === String(modelId));
  const isSerial = selectedModel?.tracking_type === "serial";
  const hasFinal = invoices.some((i) => i.kind === "final");

  function reload() {
    api.listActivityItems(activityId).then(setItems).catch((e) => setError(e.message));
    api.listInvoices({ activity_id: activityId }).then(setInvoices).catch(() => {});
  }

  useEffect(() => {
    reload();
    api.listProductModels().then(setModels).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activityId]);

  // when a serial model is chosen, load its in-warehouse units
  useEffect(() => {
    setStockItemId("");
    setQuantity("");
    if (isSerial && modelId) {
      api
        .listStockItems({ model_id: modelId, status: "warehouse" })
        .then(setUnits)
        .catch(() => setUnits([]));
    } else {
      setUnits([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelId]);

  const modelName = (it) => {
    if (it.stock_item_id) return `تک‌کالا #${it.stock_item_id}`;
    const m = models.find((x) => x.id === it.product_model_id);
    return `${m ? m.name : "#" + it.product_model_id} × ${it.quantity}`;
  };

  async function addItem(e) {
    e.preventDefault();
    setError("");
    try {
      const body = { price: Number(price) };
      if (isSerial) {
        if (!stockItemId) throw new Error("یک تک‌کالا انتخاب کنید");
        body.stock_item_id = Number(stockItemId);
      } else {
        body.product_model_id = Number(modelId);
        body.quantity = Number(quantity);
      }
      await api.addActivityItem(activityId, body);
      setModelId("");
      setPrice("");
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  async function removeItem(itemId) {
    await api.deleteActivityItem(activityId, itemId);
    reload();
  }

  async function issue(kind) {
    setError("");
    try {
      await api.createInvoice({
        activity_id: activityId,
        kind,
        settlement_due_date: dueDate || null,
      });
      setDueDate("");
      reload();
      onChanged && onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  async function finalize(id) {
    setError("");
    try {
      await api.finalizeInvoice(id);
      reload();
      onChanged && onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  const total = items.reduce((s, it) => s + Number(it.price), 0);

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <h2 style={{ marginTop: 0 }}>اقلام و فاکتور — فعالیت #{activityId}</h2>

      <table>
        <thead>
          <tr>
            <th>قلم</th>
            <th>قیمت</th>
            {canWrite && <th></th>}
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id}>
              <td>{modelName(it)}</td>
              <td>{Number(it.price).toLocaleString("fa-IR")}</td>
              {canWrite && (
                <td>
                  <button
                    className="secondary"
                    style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                    onClick={() => removeItem(it.id)}
                    disabled={hasFinal}
                  >
                    حذف
                  </button>
                </td>
              )}
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={canWrite ? 3 : 2} style={{ textAlign: "center", opacity: 0.6 }}>
                قلمی افزوده نشده
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div style={{ textAlign: "left", marginTop: 6, fontWeight: 700 }}>
        جمع کل: {total.toLocaleString("fa-IR")}
      </div>

      {canWrite && !hasFinal && (
        <form className="row" style={{ gap: 8, marginTop: 12, flexWrap: "wrap" }} onSubmit={addItem}>
          <select value={modelId} onChange={(e) => setModelId(e.target.value)} required style={{ width: 200 }}>
            <option value="">— انتخاب کالا —</option>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.tracking_type === "serial" ? "سریال‌دار" : "بدون سریال"})
              </option>
            ))}
          </select>
          {isSerial ? (
            <select value={stockItemId} onChange={(e) => setStockItemId(e.target.value)} style={{ width: 180 }}>
              <option value="">— تک‌کالا —</option>
              {units.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.serial_number}
                </option>
              ))}
            </select>
          ) : (
            selectedModel && (
              <input
                type="number"
                min="0"
                step="any"
                placeholder={`مقدار (${selectedModel.unit_of_measure})`}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                style={{ width: 140 }}
                required
              />
            )
          )}
          <input
            type="number"
            min="0"
            placeholder="قیمت این قلم"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            style={{ width: 150 }}
            required
          />
          <button type="submit" style={{ width: "auto", marginTop: 0 }}>
            افزودن قلم
          </button>
        </form>
      )}

      <hr style={{ border: "none", borderTop: "1px solid var(--line-soft)", margin: "18px 0" }} />

      <h3 style={{ margin: "0 0 8px", color: "var(--navy)" }}>فاکتورها</h3>
      <table>
        <thead>
          <tr>
            <th>شناسه</th>
            <th>نوع</th>
            <th>مبلغ</th>
            <th>وضعیت</th>
            <th>تصفیه حساب</th>
            {canWrite && <th></th>}
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => (
            <tr key={inv.id}>
              <td>{inv.id}</td>
              <td>
                <span className="badge">{INVOICE_KIND_FA[inv.kind]}</span>
              </td>
              <td>{Number(inv.total_amount).toLocaleString("fa-IR")}</td>
              <td>{INVOICE_STATUS_FA[inv.status]}</td>
              <td>{inv.settlement_due_date || "—"}</td>
              {canWrite && (
                <td>
                  {inv.kind === "proforma" && !hasFinal && (
                    <button
                      style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                      onClick={() => finalize(inv.id)}
                    >
                      نهایی‌سازی
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
          {invoices.length === 0 && (
            <tr>
              <td colSpan={canWrite ? 6 : 5} style={{ textAlign: "center", opacity: 0.6 }}>
                فاکتوری صادر نشده
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {canWrite && (
        <div className="row" style={{ gap: 8, marginTop: 12, flexWrap: "wrap" }}>
          <label style={{ margin: 0 }}>
            تاریخ تصفیه حساب:{" "}
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} style={{ width: 170 }} />
          </label>
          <button
            className="secondary"
            style={{ width: "auto", marginTop: 0 }}
            onClick={() => issue("proforma")}
            disabled={items.length === 0}
          >
            صدور پیش‌فاکتور
          </button>
          <button
            style={{ width: "auto", marginTop: 0 }}
            onClick={() => issue("final")}
            disabled={items.length === 0 || hasFinal}
          >
            صدور فاکتور نهایی
          </button>
        </div>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  );
}
