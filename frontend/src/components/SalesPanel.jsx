import React, { useEffect, useState } from "react";
import { api } from "../api";
import { INVOICE_STATUS_FA } from "../labels";
import InvoiceEditor from "./InvoiceEditor";
import InvoiceLines from "./InvoiceLines";

// Invoicing panel for one activity: its proformas and final invoices, each with
// its own line items. Create as many of either as needed; convert a proforma
// into a final invoice with editable prices.
export default function SalesPanel({ activityId, canWrite, onChanged }) {
  const [invoices, setInvoices] = useState([]);
  const [error, setError] = useState("");
  const [editor, setEditor] = useState(null); // {kind, initialItems?, sourceProformaId?}
  const [openId, setOpenId] = useState(null);

  function reload() {
    api
      .listInvoices({ activity_id: activityId })
      .then(setInvoices)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activityId]);

  const proformas = invoices.filter((i) => i.kind === "proforma");
  const finals = invoices.filter((i) => i.kind === "final");
  const isConverted = (pfId) => finals.some((f) => f.source_proforma_id === pfId);

  function afterSave() {
    setEditor(null);
    reload();
    onChanged && onChanged();
  }

  async function convert(pf) {
    // prefill the final-invoice form with this proforma's lines (editable prices)
    const full = await api.getInvoice(pf.id);
    setEditor({
      kind: "final",
      sourceProformaId: pf.id,
      initialItems: full.items,
    });
  }

  async function remove(id) {
    setError("");
    try {
      await api.deleteInvoice(id);
      reload();
      onChanged && onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  async function setStatus(id, status) {
    setError("");
    try {
      await api.updateInvoice(id, { status });
      reload();
      onChanged && onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  function InvoiceTable({ rows, isProforma }) {
    return (
      <table>
        <thead>
          <tr>
            <th>شناسه</th>
            <th>مبلغ</th>
            <th>وضعیت</th>
            <th>تصفیه</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((inv) => (
            <React.Fragment key={inv.id}>
              <tr>
                <td>
                  #{inv.id}
                  {inv.source_proforma_id && (
                    <span style={{ opacity: 0.6, fontSize: 12 }}>
                      {" "}
                      (از پیش‌فاکتور #{inv.source_proforma_id})
                    </span>
                  )}
                  {isProforma && isConverted(inv.id) && (
                    <span className="badge" style={{ marginInlineStart: 6 }}>
                      تبدیل‌شده
                    </span>
                  )}
                </td>
                <td>{Number(inv.total_amount).toLocaleString("fa-IR")}</td>
                <td>{INVOICE_STATUS_FA[inv.status]}</td>
                <td>{inv.settlement_due_date || "—"}</td>
                <td>
                  <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
                    <button
                      className="secondary"
                      style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                      onClick={() => setOpenId(openId === inv.id ? null : inv.id)}
                    >
                      ردیف‌ها
                    </button>
                    {canWrite && isProforma && (
                      <button
                        style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                        onClick={() => convert(inv)}
                      >
                        تبدیل به فاکتور
                      </button>
                    )}
                    {canWrite && isProforma && (
                      <button
                        className="secondary"
                        style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                        onClick={() => remove(inv.id)}
                      >
                        حذف
                      </button>
                    )}
                    {canWrite && !isProforma && inv.status !== "paid" && (
                      <button
                        className="secondary"
                        style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                        onClick={() => setStatus(inv.id, "paid")}
                      >
                        ثبت پرداخت
                      </button>
                    )}
                  </div>
                </td>
              </tr>
              {openId === inv.id && (
                <tr>
                  <td colSpan={5} style={{ background: "var(--bg-soft, #fafafa)" }}>
                    <InvoiceLines items={inv.items} />
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} style={{ textAlign: "center", opacity: 0.6 }}>
                موردی نیست
              </td>
            </tr>
          )}
        </tbody>
      </table>
    );
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <h2 style={{ marginTop: 0 }}>پیش‌فاکتور و فاکتور — فعالیت #{activityId}</h2>

      <h3 style={{ margin: "6px 0", color: "var(--navy)" }}>پیش‌فاکتورها</h3>
      <InvoiceTable rows={proformas} isProforma />

      <hr style={{ border: "none", borderTop: "1px solid var(--line-soft)", margin: "18px 0" }} />

      <h3 style={{ margin: "6px 0", color: "var(--navy)" }}>فاکتورها</h3>
      <InvoiceTable rows={finals} isProforma={false} />

      {editor && (
        <InvoiceEditor
          activityId={activityId}
          kind={editor.kind}
          initialItems={editor.initialItems}
          sourceProformaId={editor.sourceProformaId}
          onSaved={afterSave}
          onCancel={() => setEditor(null)}
        />
      )}

      {error && <div className="error">{error}</div>}
    </div>
  );
}
