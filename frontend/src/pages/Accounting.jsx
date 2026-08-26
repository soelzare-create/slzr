import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, rows, toman } from "../api";
import { Avatar, Icon, Modal } from "../ui.jsx";

const TYPE_FA = { ASSET: "دارایی", LIABILITY: "بدهی", EQUITY: "سرمایه", INCOME: "درآمد", EXPENSE: "هزینه" };

export default function Accounting() {
  const [params, setParams] = useSearchParams();
  const [tab, setTab] = useState(params.get("tab") === "docs" ? "docs" : "balance");
  const [docModal, setDocModal] = useState(null); // {type, party}
  const [reloadKey, setReloadKey] = useState(0);

  // Deep link from a customer/supplier card: ?doc=receipt&party=ID
  useEffect(() => {
    const doc = params.get("doc");
    if (doc) {
      setTab("docs");
      setDocModal({ type: doc, party: params.get("party") || "" });
      params.delete("doc"); params.delete("party"); params.delete("tab");
      setParams(params, { replace: true });
    }
  }, []); // eslint-disable-line

  const TABS = [
    ["balance", "ترازنامه"], ["docs", "اسناد مالی"], ["ledger", "دفتر کل"],
    ["parties", "مانده طرف‌حساب‌ها"], ["journal", "اسناد سیستمی"],
  ];

  return (
    <div>
      <div className="toolbar">
        <h1 className="page-title">حسابداری</h1>
        {tab === "docs" && (
          <button className="btn primary" onClick={() => setDocModal({ type: "expense", party: "" })}>
            <Icon name="plus" size={16} color="#fff" /> سند مالی جدید
          </button>
        )}
      </div>
      <div className="seg" style={{ display: "inline-flex", marginBottom: 18 }}>
        {TABS.map(([k, l]) => (
          <button key={k} className={tab === k ? "active" : ""} onClick={() => setTab(k)}>{l}</button>
        ))}
      </div>

      {tab === "balance" && <BalanceSheet />}
      {tab === "docs" && <FinanceDocs reloadKey={reloadKey} />}
      {tab === "ledger" && <Ledger />}
      {tab === "parties" && <PartyBalances />}
      {tab === "journal" && <Journal />}

      {docModal && <FinanceDocModal init={docModal} onClose={() => setDocModal(null)}
        onSaved={() => { setDocModal(null); setTab("docs"); setReloadKey((k) => k + 1); }} />}
    </div>
  );
}

function useData(path, dep) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => { setData(null); api.get(path).then(setData).catch((e) => setError(e.message)); }, [path, dep]);
  return { data, error };
}

// ---- Financial documents (expenses + payments) ---------------------------
function FinanceDocs({ reloadKey }) {
  const [docs, setDocs] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.get("/expenses"), api.get("/payments")])
      .then(([ex, py]) => {
        const items = [
          ...rows(ex).map((e) => ({ ...e, _t: "expense" })),
          ...rows(py).map((p) => ({ ...p, _t: "payment" })),
        ].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
        setDocs(items);
      })
      .catch((e) => setError(e.message));
  }, [reloadKey]);

  if (error) return <div className="error">{error}</div>;
  if (!docs) return <div className="empty">در حال بارگذاری…</div>;

  function meta(d) {
    if (d._t === "expense") {
      return { icon: "pay", color: "#e0483d", bg: "#fbe8e6", sign: "−",
        title: `هزینهٔ ${d.category}`, sub: `${d.number} · ${d.kind_display}`, who: d.owner_name };
    }
    const receipt = d.direction === "RECEIPT";
    return {
      icon: receipt ? "receive" : "pay", color: receipt ? "#10a86b" : "#e0483d",
      bg: receipt ? "#e5f6ee" : "#fbe8e6", sign: receipt ? "+" : "−",
      title: `${d.direction_display} ${receipt ? "از" : "به"} ${d.party_name}`,
      sub: `${d.number} · ${d.direction_display}`, who: d.party_name,
    };
  }

  return (
    <div className="card" style={{ padding: "6px 20px 10px" }}>
      {docs.length === 0 ? <div className="empty">هنوز سند مالی‌ای ثبت نشده. با «سند مالی جدید» شروع کنید.</div> : (
        <table>
          <tbody>
            {docs.map((d) => {
              const m = meta(d);
              const cancelled = d.status === "CANCELLED";
              return (
                <tr key={d._t + d.id} style={cancelled ? { opacity: .5 } : undefined}>
                  <td style={{ width: 46, border: docs[0] === d ? "none" : undefined }}>
                    <div className="avatar" style={{ width: 34, height: 34, borderRadius: 10, background: m.bg }}>
                      <Icon name={m.icon} size={16} color={m.color} />
                    </div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: 13.5 }}>{m.title}{cancelled && <span className="badge red" style={{ marginInlineStart: 8 }}>ابطال</span>}</div>
                    <div className="muted" style={{ fontSize: 11.5 }}>{m.sub} · {d.date}</div>
                  </td>
                  <td className="num" style={{ textAlign: "left", fontWeight: 700, color: m.color, width: 160 }}>{m.sign} {toman(d.amount)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

function FinanceDocModal({ init, onClose, onSaved }) {
  const [type, setType] = useState(init.type === "receipt" || init.type === "payment" ? init.type : "expense");
  const [kind, setKind] = useState("DIRECT");
  const [cashAccounts, setCashAccounts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState({
    amount: "", category: "", account: "", party: init.party || "", description: "",
  });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/accounts/cash").then((d) => {
      const acc = rows(d);
      setCashAccounts(acc);
      setForm((f) => ({ ...f, account: f.account || (acc[0] && acc[0].id) || "" }));
    }).catch(() => {});
    api.get("/parties?role=customer").then((d) => setCustomers(rows(d))).catch(() => {});
    api.get("/parties?role=supplier").then((d) => setSuppliers(rows(d))).catch(() => {});
  }, []);

  const partyOptions = type === "payment" ? suppliers : customers;

  async function save(e) {
    e.preventDefault();
    setError(null); setBusy(true);
    try {
      if (type === "expense") {
        await api.post("/expenses", {
          kind, category: form.category, amount: Number(form.amount),
          paid_from: Number(form.account), description: form.description,
          party: form.party ? Number(form.party) : null,
        });
      } else {
        await api.post("/payments", {
          direction: type === "receipt" ? "RECEIPT" : "PAYMENT",
          party: Number(form.party), amount: Number(form.amount),
          account: Number(form.account), description: form.description,
        });
      }
      onSaved();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  const TYPES = [["expense", "هزینه", "pay"], ["receipt", "دریافت", "receive"], ["payment", "پرداخت", "pay"]];

  return (
    <Modal title="ثبت سند مالی" icon="doc" onClose={onClose}>
      <form onSubmit={save}>
        {error && <div className="error">{error}</div>}
        <div className="seg" style={{ marginBottom: 18 }}>
          {TYPES.map(([k, l, ic]) => (
            <button type="button" key={k} className={type === k ? "active" : ""} onClick={() => setType(k)}>
              <Icon name={ic} size={15} color={type === k ? "#10151f" : "#6b7688"} />{l}
            </button>
          ))}
        </div>

        {type === "expense" && (
          <div className="field">
            <label>نوع هزینه</label>
            <div className="seg">
              <button type="button" className={kind === "DIRECT" ? "active" : ""} onClick={() => setKind("DIRECT")}>مستقیم</button>
              <button type="button" className={kind === "OVERHEAD" ? "active" : ""} onClick={() => setKind("OVERHEAD")}>سربار</button>
            </div>
          </div>
        )}

        {type !== "expense" && (
          <div className="field">
            <label>{type === "payment" ? "تأمین‌کننده" : "مشتری"}</label>
            <select value={form.party} onChange={(e) => setForm({ ...form, party: e.target.value })} required>
              <option value="">— انتخاب —</option>
              {partyOptions.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        )}

        {type === "expense" && (
          <div className="field">
            <label>دستهٔ هزینه</label>
            <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
              placeholder="اجاره، حقوق، حمل‌ونقل…" required />
          </div>
        )}

        <div className="row">
          <div className="field">
            <label>مبلغ (تومان)</label>
            <input type="number" min="0" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          </div>
          <div className="field">
            <label>{type === "expense" ? "پرداخت از" : (type === "receipt" ? "دریافت به" : "پرداخت از")}</label>
            <select value={form.account} onChange={(e) => setForm({ ...form, account: e.target.value })} required>
              {cashAccounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
        </div>

        <div className="field">
          <label>شرح</label>
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>

        <button className="btn primary" style={{ width: "100%" }} disabled={busy}>
          {busy ? "در حال ثبت…" : "ثبت و صدور سند خودکار"}
        </button>
      </form>
    </Modal>
  );
}

// ---- Reports (unchanged logic, modern styling) ---------------------------
function BalanceSheet() {
  const { data, error } = useData("/reports/balance-sheet");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  return (
    <div className="row">
      <div className="card" style={{ flex: 1 }}>
        <b style={{ fontSize: 15 }}>ترازنامه</b>
        <table style={{ marginTop: 10 }}>
          <tbody>
            <tr><td className="muted" style={{ border: "none" }}>دارایی‌ها</td><td className="num" style={{ border: "none", fontWeight: 600 }}>{toman(data.assets)}</td></tr>
            <tr><td className="muted">بدهی‌ها</td><td className="num" style={{ fontWeight: 600 }}>{toman(data.liabilities)}</td></tr>
            <tr><td className="muted">سرمایه</td><td className="num" style={{ fontWeight: 600 }}>{toman(data.equity)}</td></tr>
          </tbody>
        </table>
      </div>
      <div className="card" style={{ flex: 1 }}>
        <b style={{ fontSize: 15 }}>سود و زیان</b>
        <table style={{ marginTop: 10 }}>
          <tbody>
            <tr><td className="muted" style={{ border: "none" }}>درآمد</td><td className="num" style={{ border: "none", fontWeight: 600, color: "var(--green)" }}>{toman(data.income)}</td></tr>
            <tr><td className="muted">هزینه</td><td className="num" style={{ fontWeight: 600, color: "var(--red)" }}>{toman(data.expense)}</td></tr>
            <tr><td style={{ fontWeight: 700 }}>سود خالص</td><td className="num" style={{ fontWeight: 700 }}>{toman(data.net_income)}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Ledger() {
  const { data, error } = useData("/reports/ledger");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  const active = data.filter((r) => r.debit || r.credit);
  return (
    <div className="card">
      <table>
        <thead><tr><th>کد</th><th>حساب</th><th>نوع</th><th>بدهکار</th><th>بستانکار</th><th>مانده</th></tr></thead>
        <tbody>
          {active.map((r) => (
            <tr key={r.code}>
              <td className="num">{r.code}</td><td>{r.name}</td><td>{TYPE_FA[r.type]}</td>
              <td className="num">{toman(r.debit)}</td><td className="num">{toman(r.credit)}</td><td className="num">{toman(r.balance)}</td>
            </tr>
          ))}
          {active.length === 0 && <tr><td colSpan={6} className="empty">هنوز سندی ثبت نشده.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function PartyBalances() {
  const { data, error } = useData("/reports/party-balances");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  return (
    <div className="card">
      <table>
        <thead><tr><th>طرف‌حساب</th><th>مانده</th><th>وضعیت</th></tr></thead>
        <tbody>
          {data.map((r) => (
            <tr key={r.party_id}>
              <td className="flex" style={{ gap: 10 }}><Avatar name={r.party_name} size={30} radius={9} />{r.party_name}</td>
              <td className="num">{toman(Math.abs(r.balance))}</td>
              <td>{r.balance > 0 ? <span className="badge blue">بدهکار به ما</span> : r.balance < 0 ? <span className="badge amber">طلبکار از ما</span> : <span className="badge gray">تسویه</span>}</td>
            </tr>
          ))}
          {data.length === 0 && <tr><td colSpan={3} className="empty">موردی نیست.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function Journal() {
  const { data, error } = useData("/journal");
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="empty">در حال بارگذاری…</div>;
  const entries = Array.isArray(data) ? data : data.results || [];
  return (
    <div>
      {entries.map((e) => (
        <div className="card" key={e.id} style={{ marginBottom: 14 }}>
          <div className="toolbar" style={{ marginBottom: 8 }}>
            <b className="num">{e.number} — {e.description}</b>
            <span className="muted">{e.date} {e.is_reversal && <span className="badge amber">سند برگشت</span>}</span>
          </div>
          <table>
            <thead><tr><th>حساب</th><th>طرف‌حساب</th><th>بدهکار</th><th>بستانکار</th></tr></thead>
            <tbody>
              {e.lines.map((l) => (
                <tr key={l.id}>
                  <td>{l.account_code} — {l.account_name}</td><td>{l.party_name || "—"}</td>
                  <td className="num">{Number(l.debit) ? toman(l.debit) : "—"}</td>
                  <td className="num">{Number(l.credit) ? toman(l.credit) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      {entries.length === 0 && <div className="card"><div className="empty">هنوز سندی ثبت نشده.</div></div>}
    </div>
  );
}
