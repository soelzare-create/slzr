import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { REFERRAL_SOURCES, PARTY_WRITE_ROLES, CONTACT_POSITIONS } from "../labels";

// One component drives both the Customers view and the Suppliers view,
// over the single `parties` table. `role` is "customer" or "supplier".
export default function Parties({ role }) {
  const { me, loading } = useMe();
  const isCustomerView = role === "customer";
  const title = isCustomerView ? "مشتری‌ها" : "تأمین‌کننده‌ها";

  const [parties, setParties] = useState([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const emptyForm = () => ({
    name: "",
    phone: "",
    address: "",
    is_customer: isCustomerView,
    is_supplier: !isCustomerView,
    referral_source: "",
  });
  const [form, setForm] = useState(emptyForm);
  // Which party's «افراد رابط» panel is currently open (by id).
  const [openId, setOpenId] = useState(null);

  const canWrite = me && PARTY_WRITE_ROLES.includes(me.role);

  function reload(search = "") {
    api
      .listParties({ role, q: search })
      .then(setParties)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (me) {
      setForm(emptyForm());
      reload();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me, role]);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    if (!form.is_customer && !form.is_supplier) {
      setError("حداقل یک نقش (مشتری یا تأمین‌کننده) را انتخاب کنید");
      return;
    }
    setBusy(true);
    try {
      await api.createParty(form);
      setForm(emptyForm());
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
          <h2 style={{ margin: 0 }}>{title}</h2>
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
              <th>نقش‌ها</th>
              {isCustomerView && <th>مدل آشنایی</th>}
              <th>افراد رابط</th>
            </tr>
          </thead>
          <tbody>
            {parties.map((p) => (
              <React.Fragment key={p.id}>
                <tr>
                  <td>{p.id}</td>
                  <td>{p.name}</td>
                  <td>{p.phone || "—"}</td>
                  <td>{p.address || "—"}</td>
                  <td>
                    {p.is_customer && <span className="badge">مشتری</span>}{" "}
                    {p.is_supplier && <span className="badge">تأمین‌کننده</span>}
                  </td>
                  {isCustomerView && (
                    <td>
                      {REFERRAL_SOURCES[p.referral_source] ||
                        p.referral_source ||
                        "—"}
                    </td>
                  )}
                  <td>
                    <button
                      className="secondary"
                      style={{ width: "auto", marginTop: 0, padding: "4px 10px" }}
                      onClick={() => setOpenId(openId === p.id ? null : p.id)}
                    >
                      {openId === p.id ? "بستن" : "افراد"}
                      {p.contacts?.length ? ` (${p.contacts.length})` : ""}
                    </button>
                  </td>
                </tr>
                {openId === p.id && (
                  <tr>
                    <td colSpan={isCustomerView ? 7 : 6} style={{ background: "rgba(0,0,0,0.02)" }}>
                      <ContactsPanel
                        party={p}
                        canWrite={canWrite}
                        onChanged={() => reload(q)}
                      />
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
            {parties.length === 0 && (
              <tr>
                <td colSpan={isCustomerView ? 7 : 6} style={{ textAlign: "center", opacity: 0.6 }}>
                  موردی نیست
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {canWrite && (
        <form className="card" style={{ marginTop: 20 }} onSubmit={onCreate}>
          <h2 style={{ marginTop: 0 }}>
            افزودن {isCustomerView ? "مشتری" : "تأمین‌کننده"}
          </h2>
          <div className="grid2">
            <div>
              <label>نام شخص یا سازمان *</label>
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
            {form.is_customer && (
              <div>
                <label>مدل آشنایی</label>
                <select
                  value={form.referral_source}
                  onChange={(e) =>
                    setForm({ ...form, referral_source: e.target.value })
                  }
                >
                  <option value="">— انتخاب —</option>
                  {Object.entries(REFERRAL_SOURCES).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="row" style={{ gap: 20, marginTop: 6 }}>
            <label className="row" style={{ gap: 6, margin: 0 }}>
              <input
                type="checkbox"
                style={{ width: "auto" }}
                checked={form.is_customer}
                onChange={(e) =>
                  setForm({ ...form, is_customer: e.target.checked })
                }
              />
              مشتری است
            </label>
            <label className="row" style={{ gap: 6, margin: 0 }}>
              <input
                type="checkbox"
                style={{ width: "auto" }}
                checked={form.is_supplier}
                onChange={(e) =>
                  setForm({ ...form, is_supplier: e.target.checked })
                }
              />
              تأمین‌کننده است
            </label>
          </div>

          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy} style={{ width: "auto" }}>
            {busy ? "در حال ثبت…" : "ثبت"}
          </button>
        </form>
      )}
    </Layout>
  );
}

// The «افراد رابط» panel for a single party: lists its contact people
// (سمت / نام / شماره / ثبت‌کننده) and — for users who may write — a form to add
// one. Position (سمت) is a required dropdown.
function ContactsPanel({ party, canWrite, onChanged }) {
  const emptyForm = () => ({ name: "", phone: "", position: "" });
  const [contacts, setContacts] = useState(party.contacts || []);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function reload() {
    api
      .listPartyContacts(party.id)
      .then(setContacts)
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [party.id]);

  async function onAdd(e) {
    e.preventDefault();
    setError("");
    if (!form.position) {
      setError("انتخاب «سمت» الزامی است");
      return;
    }
    setBusy(true);
    try {
      await api.addPartyContact(party.id, form);
      setForm(emptyForm());
      reload();
      onChanged && onChanged();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id) {
    setError("");
    try {
      await api.deletePartyContact(party.id, id);
      reload();
      onChanged && onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <h3 style={{ margin: "4px 0 10px" }}>افراد رابطِ «{party.name}»</h3>
      <table>
        <thead>
          <tr>
            <th>سمت</th>
            <th>نام</th>
            <th>شماره تماس</th>
            <th>ثبت‌کننده</th>
            {canWrite && <th></th>}
          </tr>
        </thead>
        <tbody>
          {contacts.map((c) => (
            <tr key={c.id}>
              <td>
                <span className="badge">
                  {CONTACT_POSITIONS[c.position] || c.position}
                </span>
              </td>
              <td>{c.name}</td>
              <td>{c.phone || "—"}</td>
              <td style={{ opacity: 0.7 }}>{c.created_by_name || "—"}</td>
              {canWrite && (
                <td>
                  <button
                    className="secondary"
                    style={{ width: "auto", marginTop: 0, padding: "2px 8px" }}
                    onClick={() => onDelete(c.id)}
                  >
                    حذف
                  </button>
                </td>
              )}
            </tr>
          ))}
          {contacts.length === 0 && (
            <tr>
              <td colSpan={canWrite ? 5 : 4} style={{ textAlign: "center", opacity: 0.6 }}>
                هنوز فرد رابطی ثبت نشده
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {canWrite && (
        <form className="row" style={{ gap: 8, marginTop: 10, flexWrap: "wrap" }} onSubmit={onAdd}>
          <input
            placeholder="نام فرد *"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            style={{ width: 160, marginTop: 0 }}
          />
          <input
            placeholder="شماره تماس"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            style={{ width: 150, marginTop: 0 }}
          />
          <select
            required
            value={form.position}
            onChange={(e) => setForm({ ...form, position: e.target.value })}
            style={{ width: 170, marginTop: 0 }}
          >
            <option value="">— سمت * —</option>
            {Object.entries(CONTACT_POSITIONS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <button type="submit" disabled={busy} style={{ width: "auto", marginTop: 0 }}>
            {busy ? "در حال ثبت…" : "افزودن فرد"}
          </button>
        </form>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}
