import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { REFERRAL_SOURCES, WRITE_ROLES } from "../labels";

const EMPTY = { name: "", phone: "", address: "", referral_source: "" };

export default function Customers() {
  const { me, loading } = useMe();
  const [customers, setCustomers] = useState([]);
  const [q, setQ] = useState("");
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const canWrite = me && WRITE_ROLES.includes(me.role);

  function reload(search = "") {
    api.listCustomers({ q: search }).then(setCustomers).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (me) reload();
  }, [me]);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.createCustomer(form);
      setForm(EMPTY);
      reload(q);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>مشتری‌ها</h2>
          <div className="row" style={{ gap: 8 }}>
            <input
              placeholder="جستجو در نام…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              style={{ width: 200 }}
            />
            <button
              className="secondary"
              style={{ width: "auto", marginTop: 0 }}
              onClick={() => reload(q)}
            >
              جستجو
            </button>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>نام</th>
              <th>شماره تماس</th>
              <th>نشانی</th>
              <th>مدل آشنایی</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.name}</td>
                <td>{c.phone || "—"}</td>
                <td>{c.address || "—"}</td>
                <td>{REFERRAL_SOURCES[c.referral_source] || c.referral_source || "—"}</td>
              </tr>
            ))}
            {customers.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", opacity: 0.6 }}>
                  موردی نیست
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {canWrite && (
        <form className="card" style={{ marginTop: 20 }} onSubmit={onCreate}>
          <h2 style={{ marginTop: 0 }}>افزودن مشتری</h2>
          <div className="grid2">
            <div>
              <label>نام مشتری یا سازمان *</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label>شماره تماس</label>
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div>
              <label>نشانی</label>
              <input
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
              />
            </div>
            <div>
              <label>مدل آشنایی</label>
              <select
                value={form.referral_source}
                onChange={(e) => setForm({ ...form, referral_source: e.target.value })}
              >
                <option value="">— انتخاب —</option>
                {Object.entries(REFERRAL_SOURCES).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy} style={{ width: "auto" }}>
            {busy ? "در حال ثبت…" : "ثبت مشتری"}
          </button>
        </form>
      )}
    </Layout>
  );
}
