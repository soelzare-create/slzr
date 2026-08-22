import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import InvoiceLines from "../components/InvoiceLines";
import InvoiceEditor from "../components/InvoiceEditor";
import { WRITE_ROLES } from "../labels";

// Standalone list of every proforma (پیش‌فاکتور) across activities.
export default function Proformas() {
  const { me, loading } = useMe();
  const [rows, setRows] = useState([]);
  const [finals, setFinals] = useState([]);
  const [activities, setActivities] = useState([]);
  const [parties, setParties] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [convert, setConvert] = useState(null); // {activityId, sourceProformaId, items}
  const [error, setError] = useState("");

  const canWrite = me && WRITE_ROLES.includes(me.role);

  function reload() {
    api.listInvoices({ kind: "proforma" }).then(setRows).catch((e) => setError(e.message));
    api.listInvoices({ kind: "final" }).then(setFinals).catch(() => {});
  }

  useEffect(() => {
    if (!me) return;
    api.listActivities().then(setActivities).catch(() => {});
    api.listParties().then(setParties).catch(() => {});
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me]);

  const partyName = (id) => parties.find((p) => p.id === id)?.name || "—";
  const customerOf = (activityId) => {
    const a = activities.find((x) => x.id === activityId);
    return a ? partyName(a.customer_id) : "—";
  };
  const isConverted = (pfId) => finals.some((f) => f.source_proforma_id === pfId);

  async function startConvert(pf) {
    setError("");
    const full = await api.getInvoice(pf.id);
    setConvert({
      activityId: pf.activity_id,
      sourceProformaId: pf.id,
      items: full.items,
    });
  }

  async function remove(id) {
    setError("");
    try {
      await api.deleteInvoice(id);
      reload();
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>پیش‌فاکتورها</h2>
        <p style={{ marginTop: 0, opacity: 0.75, fontSize: 14 }}>
          برای ساختن پیش‌فاکتور جدید، از صفحه‌ی «فعالیت‌ها» یک فعالیت را باز کنید و
          «ثبت پیش‌فاکتور جدید» را بزنید. اینجا همه‌ی پیش‌فاکتورها را می‌بینید و
          می‌توانید هرکدام را که مشتری تأیید کرد به فاکتور تبدیل کنید.
        </p>
        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>مشتری</th>
              <th>مبلغ</th>
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
                    {isConverted(inv.id) && (
                      <span className="badge" style={{ marginInlineStart: 6 }}>
                        تبدیل‌شده
                      </span>
                    )}
                  </td>
                  <td>{customerOf(inv.activity_id)}</td>
                  <td>{Number(inv.total_amount).toLocaleString("fa-IR")}</td>
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
                      {canWrite && (
                        <button
                          style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => startConvert(inv)}
                        >
                          تبدیل به فاکتور
                        </button>
                      )}
                      {canWrite && (
                        <button
                          className="secondary"
                          style={{ width: "auto", marginTop: 0, padding: "3px 10px" }}
                          onClick={() => remove(inv.id)}
                        >
                          حذف
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
                {openId === inv.id && (
                  <tr>
                    <td colSpan={5}>
                      <InvoiceLines items={inv.items} />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", opacity: 0.6 }}>
                  پیش‌فاکتوری ثبت نشده
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {error && <div className="error">{error}</div>}
      </div>

      {convert && (
        <InvoiceEditor
          activityId={convert.activityId}
          kind="final"
          initialItems={convert.items}
          sourceProformaId={convert.sourceProformaId}
          onSaved={() => {
            setConvert(null);
            reload();
          }}
          onCancel={() => setConvert(null)}
        />
      )}
    </Layout>
  );
}
