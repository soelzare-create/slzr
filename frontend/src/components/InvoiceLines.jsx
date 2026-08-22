import React from "react";

// Read-only table of an invoice's line items.
export default function InvoiceLines({ items }) {
  if (!items || items.length === 0) {
    return <div style={{ opacity: 0.6, padding: "6px 0" }}>ردیفی ثبت نشده</div>;
  }
  const total = items.reduce((s, it) => s + Number(it.line_total), 0);
  return (
    <table>
      <thead>
        <tr>
          <th>شرح</th>
          <th>تعداد</th>
          <th>قیمت واحد</th>
          <th>جمع ردیف</th>
        </tr>
      </thead>
      <tbody>
        {items.map((it) => (
          <tr key={it.id}>
            <td>{it.description}</td>
            <td>{Number(it.quantity).toLocaleString("fa-IR")}</td>
            <td>{Number(it.unit_price).toLocaleString("fa-IR")}</td>
            <td>{Number(it.line_total).toLocaleString("fa-IR")}</td>
          </tr>
        ))}
        <tr>
          <td colSpan={3} style={{ textAlign: "left", fontWeight: 700 }}>
            جمع کل
          </td>
          <td style={{ fontWeight: 700 }}>{total.toLocaleString("fa-IR")}</td>
        </tr>
      </tbody>
    </table>
  );
}
