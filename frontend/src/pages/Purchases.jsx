import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { PURCHASE_STATUS_FA, PURCHASE_WRITE_ROLES } from "../labels";

// فاز ۴B — ثبت خرید از تأمین‌کننده. قرینه‌ی سمت فروش: هر خرید چند قلم دارد؛
// ثبتِ خرید، کالا را وارد انبار و «خرج» را در حسابداری ثبت می‌کند.
export default function Purchases() {
  const { me, loading } = useMe();
  const [purchases, setPurchases] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [models, setModels] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // header of the purchase being drafted
  const [supplierId, setSupplierId] = useState("");
  const [reference, setReference] = useState("");
  const [dueDate, setDueDate] = useState("");

  // line being composed + the collected lines
  const [itemName, setItemName] = useState("");
  const [serial, setSerial] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unitCost, setUnitCost] = useState("");
  const [lines, setLines] = useState([]);

  const canWrite = me && PURCHASE_WRITE_ROLES.includes(me.role);
  const supplierName = useMemo(() => {
    const m = {};
    suppliers.forEach((s) => (m[s.id] = s.name));
    return m;
  }, [suppliers]);

  // match the typed name against an existing product (pick), else it's a new item
  const matched = models.find(
    (m) => m.name.trim().toLowerCase() === itemName.trim().toLowerCase()
  );
  const isSerial = matched && !matched.is_service && matched.tracking_type === "serial";

  function reload() {
    api.listPurchases().then(setPurchases).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!me) return;
    reload();
    api.listParties({ role: "supplier" }).then(setSuppliers).catch(() => {});
    api.listProductModels().then(setModels).catch(() => {});
  }, [me]);

  function addLine(e) {
    e.preventDefault();
    setError("");
    if (!itemName.trim()) return setError("نام کالا یا خدمت را وارد کنید");
    if (!unitCost) return setError("بهای واحد را وارد کنید");
    const line = { unit_cost: Number(unitCost) };
    if (matched) {
      line.product_model_id = matched.id;
      line._name = matched.name;
      if (isSerial) {
        if (!serial) return setError("برای کالای سریال‌دار، شماره سریال لازم است");
        line.serial_number = serial;
        line._label = `سریال ${serial}`;
        line._total = Number(unitCost);
      } else {
        if (!quantity) return setError("مقدار را وارد کنید");
        line.quantity = Number(quantity);
        line._label = `${quantity} ${matched.unit_of_measure || ""}`;
        line._total = Number(unitCost) * Number(quantity);
      }
    } else {
      // a new free item / service — will be auto-registered in the catalog
      if (!quantity) return setError("مقدار را وارد کنید");
      line.description = itemName.trim();
      line.quantity = Number(quantity);
      line._name = `${itemName.trim()} (جدید)`;
      line._label = String(quantity);
      line._total = Number(unitCost) * Number(quantity);
    }
    setLines([...lines, line]);
    setItemName("");
    setSerial("");
    setQuantity("");
    setUnitCost("");
  }

  function removeLine(i) {
    setLines(lines.filter((_, idx) => idx !== i));
  }

  const draftTotal = lines.reduce((s, l) => s + l._total, 0);

  async function submitPurchase(e) {
    e.preventDefault();
    setError("");
    if (!supplierId) return setError("تأمین‌کننده را انتخاب کنید");
    if (lines.length === 0) return setError("حداقل یک قلم اضافه کنید");
    setBusy(true);
    try {
      await api.createPurchase({
        supplier_id: Number(supplierId),
        reference: reference || null,
        settlement_due_date: dueDate || null,
        items: lines.map(({ product_model_id, description, serial_number, quantity, unit_cost }) => ({
          product_model_id: product_model_id ?? null,
          description: description || null,
          serial_number: serial_number || null,
          quantity: quantity ?? null,
          unit_cost,
        })),
      });
      setSupplierId("");
      setReference("");
      setDueDate("");
      setLines([]);
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function markPaid(id) {
    setError("");
    try {
      await api.updatePurchase(id, { status: "paid" });
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>خریدها</h2>
        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>تأمین‌کننده</th>
              <th>شماره سند</th>
              <th>مبلغ کل</th>
              <th>وضعیت</th>
              <th>تصفیه حساب</th>
              {canWrite && <th></th>}
            </tr>
          </thead>
          <tbody>
            {purchases.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{supplierName[p.supplier_id] || `#${p.supplier_id}`}</td>
                <td>{p.reference || "—"}</td>
                <td>{Number(p.total_amount).toLocaleString("fa-IR")}</td>
                <td>{PURCHASE_STATUS_FA[p.status] || p.status}</td>
                <td>{p.settlement_due_date || "—"}</td>
                {canWrite && (
                  <td>
                    {p.status !== "paid" && (
                      <button
                        className="secondary"
                        style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                        onClick={() => markPaid(p.id)}
                      >
                        پرداخت شد
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {purchases.length === 0 && (
              <tr>
                <td colSpan={canWrite ? 7 : 6} style={{ textAlign: "center", opacity: 0.6 }}>
                  خریدی ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {canWrite && (
        <div className="card" style={{ marginTop: 20 }}>
          <h2 style={{ marginTop: 0 }}>ثبت خرید جدید</h2>
          <div className="grid2">
            <div>
              <label>تأمین‌کننده *</label>
              <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} required>
                <option value="">— انتخاب —</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>شماره سند فروشنده</label>
              <input value={reference} onChange={(e) => setReference(e.target.value)} />
            </div>
            <div>
              <label>تاریخ تصفیه حساب</label>
              <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </div>
          </div>

          <h3 style={{ margin: "16px 0 8px", color: "var(--navy)" }}>اقلام خرید</h3>
          <table>
            <thead>
              <tr>
                <th>کالا</th>
                <th>مقدار / سریال</th>
                <th>بهای واحد</th>
                <th>جمع</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={i}>
                  <td>{l._name}</td>
                  <td>{l._label}</td>
                  <td>{Number(l.unit_cost).toLocaleString("fa-IR")}</td>
                  <td>{l._total.toLocaleString("fa-IR")}</td>
                  <td>
                    <button
                      className="secondary"
                      style={{ width: "auto", marginTop: 0, padding: "2px 8px" }}
                      onClick={() => removeLine(i)}
                    >
                      حذف
                    </button>
                  </td>
                </tr>
              ))}
              {lines.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", opacity: 0.6 }}>
                    قلمی افزوده نشده
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          <div style={{ textAlign: "left", marginTop: 6, fontWeight: 700 }}>
            جمع کل: {draftTotal.toLocaleString("fa-IR")}
          </div>

          <form className="row" style={{ gap: 8, marginTop: 12, flexWrap: "wrap" }} onSubmit={addLine}>
            <input
              list="purchase-products"
              placeholder="کالا از انبار یا مورد جدید…"
              value={itemName}
              onChange={(e) => setItemName(e.target.value)}
              style={{ width: 220 }}
            />
            <datalist id="purchase-products">
              {models.map((m) => (
                <option key={m.id} value={m.name}>
                  {m.is_service ? "خدمت" : m.tracking_type === "serial" ? "سریال‌دار" : "کالا"}
                  {m.part_number ? ` · ${m.part_number}` : ""}
                </option>
              ))}
            </datalist>
            {isSerial ? (
              <input
                placeholder="شماره سریال دریافتی"
                value={serial}
                onChange={(e) => setSerial(e.target.value)}
                style={{ width: 170 }}
              />
            ) : (
              <input
                type="number"
                min="0"
                step="any"
                placeholder={`مقدار${matched ? ` (${matched.unit_of_measure})` : ""}`}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                style={{ width: 150 }}
              />
            )}
            <input
              type="number"
              min="0"
              step="any"
              placeholder="بهای واحد"
              value={unitCost}
              onChange={(e) => setUnitCost(e.target.value)}
              style={{ width: 150 }}
            />
            <button type="submit" className="secondary" style={{ width: "auto", marginTop: 0 }}>
              افزودن قلم
            </button>
          </form>
          <p style={{ opacity: 0.65, fontSize: 13, marginTop: 6 }}>
            نام کالای موجود را انتخاب کنید تا وارد انبار شود، یا نام یک مورد جدید
            (خدمت/کالا) را تایپ کنید تا خودکار در کاتالوگ ثبت شود.
          </p>

          {error && <div className="error">{error}</div>}
          <button
            onClick={submitPurchase}
            disabled={busy || lines.length === 0}
            style={{ width: "auto", marginTop: 14 }}
          >
            {busy ? "در حال ثبت…" : "ثبت خرید"}
          </button>
        </div>
      )}
      {!canWrite && error && <div className="error">{error}</div>}
    </Layout>
  );
}
