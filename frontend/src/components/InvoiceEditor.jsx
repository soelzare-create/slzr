import React, { useEffect, useState } from "react";
import { api } from "../api";
import { INVOICE_KIND_FA } from "../labels";

// Reusable line-item editor for creating a proforma or a final invoice.
// Used from the activity panel (blank) and from "convert" (prefilled from a
// proforma). Each row: description + optional warehouse product + qty + unit price.
function emptyLine() {
  return { description: "", product_model_id: "", quantity: "1", unit_price: "" };
}

export default function InvoiceEditor({
  activityId,
  kind, // "proforma" | "final"
  initialItems, // optional array to prefill (convert flow)
  sourceProformaId, // optional
  onSaved,
  onCancel,
}) {
  const [lines, setLines] = useState(
    initialItems && initialItems.length
      ? initialItems.map((it) => ({
          description: it.description || "",
          product_model_id: it.product_model_id ? String(it.product_model_id) : "",
          quantity: String(it.quantity ?? "1"),
          unit_price: String(it.unit_price ?? ""),
        }))
      : [emptyLine()]
  );
  const [dueDate, setDueDate] = useState("");
  const [products, setProducts] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // Only non-serial (quantity) goods can be linked to a line for stock-out.
    api
      .listProductModels()
      .then((all) => setProducts(all.filter((m) => m.tracking_type === "quantity")))
      .catch(() => {});
  }, []);

  function setLine(idx, patch) {
    setLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }
  function addRow() {
    setLines((prev) => [...prev, emptyLine()]);
  }
  function removeRow(idx) {
    setLines((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev));
  }

  function onPickProduct(idx, value) {
    const patch = { product_model_id: value };
    const p = products.find((m) => String(m.id) === String(value));
    if (p) {
      // prefill description + price from the catalog, but keep them editable
      const cur = lines[idx];
      if (!cur.description) patch.description = p.name;
      if (!cur.unit_price) patch.unit_price = String(p.base_price ?? "");
    }
    setLine(idx, patch);
  }

  const lineTotal = (l) => (Number(l.quantity) || 0) * (Number(l.unit_price) || 0);
  const grandTotal = lines.reduce((s, l) => s + lineTotal(l), 0);

  async function save() {
    setError("");
    const items = lines
      .filter((l) => l.description.trim() !== "")
      .map((l) => ({
        description: l.description.trim(),
        product_model_id: l.product_model_id ? Number(l.product_model_id) : null,
        quantity: Number(l.quantity) || 0,
        unit_price: Number(l.unit_price) || 0,
      }));
    if (items.length === 0) {
      setError("حداقل یک ردیف با شرح لازم است");
      return;
    }
    if (items.some((it) => it.quantity <= 0)) {
      setError("تعداد هر ردیف باید بزرگ‌تر از صفر باشد");
      return;
    }
    setBusy(true);
    try {
      await api.createInvoice({
        activity_id: Number(activityId),
        kind,
        settlement_due_date: dueDate || null,
        source_proforma_id: sourceProformaId || null,
        items,
      });
      onSaved && onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card" style={{ marginTop: 16, border: "1px solid var(--navy)" }}>
      <h3 style={{ marginTop: 0 }}>
        {sourceProformaId
          ? `تبدیل پیش‌فاکتور #${sourceProformaId} به فاکتور`
          : `ثبت ${INVOICE_KIND_FA[kind]} جدید`}
      </h3>

      <table>
        <thead>
          <tr>
            <th>شرح (کالا یا خدمت)</th>
            <th>کالای انبار (اختیاری)</th>
            <th>تعداد</th>
            <th>قیمت واحد</th>
            <th>جمع ردیف</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {lines.map((l, idx) => (
            <tr key={idx}>
              <td>
                <input
                  placeholder="مثلاً سرور HP یا خدمات نصب"
                  value={l.description}
                  onChange={(e) => setLine(idx, { description: e.target.value })}
                  style={{ minWidth: 180 }}
                />
              </td>
              <td>
                <select
                  value={l.product_model_id}
                  onChange={(e) => onPickProduct(idx, e.target.value)}
                  style={{ minWidth: 150 }}
                >
                  <option value="">— بدون کسر انبار —</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({Number(p.current_stock).toLocaleString("fa-IR")}{" "}
                      {p.unit_of_measure})
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={l.quantity}
                  onChange={(e) => setLine(idx, { quantity: e.target.value })}
                  style={{ width: 80 }}
                />
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={l.unit_price}
                  onChange={(e) => setLine(idx, { unit_price: e.target.value })}
                  style={{ width: 130 }}
                />
              </td>
              <td>{lineTotal(l).toLocaleString("fa-IR")}</td>
              <td>
                <button
                  type="button"
                  className="secondary"
                  style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                  onClick={() => removeRow(idx)}
                  disabled={lines.length === 1}
                >
                  حذف
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="row" style={{ gap: 12, marginTop: 10, flexWrap: "wrap" }}>
        <button
          type="button"
          className="secondary"
          style={{ width: "auto", marginTop: 0 }}
          onClick={addRow}
        >
          + افزودن ردیف
        </button>
        <label style={{ margin: 0 }}>
          تاریخ تصفیه حساب:{" "}
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            style={{ width: 160 }}
          />
        </label>
        <span style={{ marginInlineStart: "auto", fontWeight: 700 }}>
          جمع کل: {grandTotal.toLocaleString("fa-IR")}
        </span>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="row" style={{ gap: 8, marginTop: 12 }}>
        <button type="button" onClick={save} disabled={busy} style={{ width: "auto" }}>
          {busy ? "در حال ثبت…" : `ثبت ${INVOICE_KIND_FA[kind]}`}
        </button>
        <button
          type="button"
          className="secondary"
          style={{ width: "auto", marginTop: 0 }}
          onClick={onCancel}
        >
          انصراف
        </button>
      </div>
    </div>
  );
}
