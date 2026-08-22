import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { INVOICE_KIND_FA } from "../labels";

// Reusable line-item editor for creating a proforma or a final invoice.
// Each row can be:
//   - a free-text service/description line (no warehouse link), or
//   - a non-serial (quantity) product  -> stock reduced by quantity on finalize, or
//   - a serial product's specific unit -> that exact device is sold on finalize.
function emptyLine() {
  return {
    description: "",
    product_model_id: "", // selected catalog model (serial or non-serial)
    stock_item_id: "", // selected serial unit (only for serial models)
    quantity: "1",
    unit_price: "",
  };
}

export default function InvoiceEditor({
  activityId, // when set, the invoice attaches to this activity
  customerMode, // when true, pick a customer and the server auto-creates an activity
  customers, // customer list for customerMode
  kind, // "proforma" | "final"
  initialItems, // optional array to prefill (convert flow)
  sourceProformaId, // optional
  onSaved,
  onCancel,
}) {
  const [products, setProducts] = useState([]);
  const [units, setUnits] = useState([]); // all serial stock units
  const [ready, setReady] = useState(false);
  const [lines, setLines] = useState([emptyLine()]);
  const [dueDate, setDueDate] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Load catalog + serial units, then build the initial line rows.
  useEffect(() => {
    Promise.all([
      api.listProductModels().catch(() => []),
      api.listStockItems({}).catch(() => []),
    ]).then(([prods, stock]) => {
      setProducts(prods);
      const serialUnits = stock.filter((s) => s.serial_number);
      setUnits(serialUnits);

      if (initialItems && initialItems.length) {
        setLines(
          initialItems.map((it) => {
            let modelId = it.product_model_id ? String(it.product_model_id) : "";
            // serial line: recover its model from the referenced unit
            if (it.stock_item_id) {
              const u = serialUnits.find((s) => s.id === it.stock_item_id);
              if (u) modelId = String(u.model_id);
            }
            return {
              description: it.description || "",
              product_model_id: modelId,
              stock_item_id: it.stock_item_id ? String(it.stock_item_id) : "",
              quantity: String(it.quantity ?? "1"),
              unit_price: String(it.unit_price ?? ""),
            };
          })
        );
      }
      setReady(true);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const productById = useMemo(() => {
    const m = {};
    for (const p of products) m[String(p.id)] = p;
    return m;
  }, [products]);

  const isSerial = (modelId) => productById[String(modelId)]?.tracking_type === "serial";

  // In-warehouse serial units for a model, plus the already-selected unit
  // (so a prefilled/convert line keeps showing its device).
  function unitsForLine(l) {
    const list = units.filter(
      (u) => String(u.model_id) === String(l.product_model_id) && u.status === "warehouse"
    );
    if (l.stock_item_id && !list.some((u) => String(u.id) === String(l.stock_item_id))) {
      const sel = units.find((u) => String(u.id) === String(l.stock_item_id));
      if (sel) list.unshift(sel);
    }
    return list;
  }

  function setLine(idx, patch) {
    setLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }
  const addRow = () => setLines((prev) => [...prev, emptyLine()]);
  const removeRow = (idx) =>
    setLines((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev));

  function onPickProduct(idx, value) {
    const p = productById[String(value)];
    const cur = lines[idx];
    const patch = { product_model_id: value, stock_item_id: "" };
    if (p) {
      if (!cur.description) patch.description = p.name;
      if (!cur.unit_price) patch.unit_price = String(p.base_price ?? "");
      if (p.tracking_type === "serial") patch.quantity = "1";
    }
    setLine(idx, patch);
  }

  const lineTotal = (l) => (Number(l.quantity) || 0) * (Number(l.unit_price) || 0);
  const grandTotal = lines.reduce((s, l) => s + lineTotal(l), 0);

  async function save() {
    setError("");
    const items = [];
    for (const l of lines) {
      if (l.description.trim() === "") continue;
      const serial = isSerial(l.product_model_id);
      if (serial && !l.stock_item_id) {
        setError(`برای کالای سریال‌دار «${l.description}» یک دستگاه از انبار انتخاب کنید`);
        return;
      }
      const item = {
        description: l.description.trim(),
        quantity: serial ? 1 : Number(l.quantity) || 0,
        unit_price: Number(l.unit_price) || 0,
        product_model_id: null,
        stock_item_id: null,
      };
      if (serial) item.stock_item_id = Number(l.stock_item_id);
      else if (l.product_model_id) item.product_model_id = Number(l.product_model_id);
      if (!serial && item.quantity <= 0) {
        setError(`تعداد ردیف «${l.description}» باید بزرگ‌تر از صفر باشد`);
        return;
      }
      items.push(item);
    }
    if (items.length === 0) {
      setError("حداقل یک ردیف با شرح لازم است");
      return;
    }
    if (customerMode && !customerId) {
      setError("مشتری را انتخاب کنید");
      return;
    }
    setBusy(true);
    try {
      await api.createInvoice({
        activity_id: activityId ? Number(activityId) : null,
        customer_id: customerMode ? Number(customerId) : null,
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

  if (!ready) return <div className="card" style={{ marginTop: 16 }}>در حال بارگذاری…</div>;

  return (
    <div className="card" style={{ marginTop: 16, border: "1px solid var(--navy)" }}>
      <h3 style={{ marginTop: 0 }}>
        {sourceProformaId
          ? `تبدیل پیش‌فاکتور #${sourceProformaId} به فاکتور`
          : `ثبت ${INVOICE_KIND_FA[kind]} جدید`}
      </h3>

      {customerMode && (
        <div style={{ marginBottom: 12 }}>
          <label>مشتری *</label>
          <select
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            style={{ maxWidth: 320 }}
          >
            <option value="">— انتخاب مشتری —</option>
            {(customers || []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <div style={{ opacity: 0.7, fontSize: 13, marginTop: 4 }}>
            برای این پیش‌فاکتور یک فعالیت «فروش کالا» به‌طور خودکار ساخته می‌شود.
          </div>
        </div>
      )}

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
          {lines.map((l, idx) => {
            const serial = isSerial(l.product_model_id);
            return (
              <tr key={idx}>
                <td>
                  <input
                    placeholder="مثلاً سرور HP یا خدمات نصب"
                    value={l.description}
                    onChange={(e) => setLine(idx, { description: e.target.value })}
                    style={{ minWidth: 160 }}
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
                        {p.name}
                        {p.tracking_type === "serial"
                          ? " (سریال‌دار)"
                          : ` (${Number(p.current_stock).toLocaleString("fa-IR")} ${p.unit_of_measure})`}
                      </option>
                    ))}
                  </select>
                  {serial && (
                    <select
                      value={l.stock_item_id}
                      onChange={(e) => setLine(idx, { stock_item_id: e.target.value })}
                      style={{ minWidth: 150, marginTop: 6 }}
                    >
                      <option value="">— انتخاب دستگاه (سریال) —</option>
                      {unitsForLine(l).map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.serial_number}
                        </option>
                      ))}
                    </select>
                  )}
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    value={serial ? 1 : l.quantity}
                    disabled={serial}
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
            );
          })}
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
