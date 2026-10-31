import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, rows, jalali } from "../api";
import { useAuth } from "../auth.jsx";
import { Avatar, Icon, Modal } from "../ui.jsx";

// Tasks (کارها): one text box. Type a sentence, press Enter — the server works
// out customer / kind / assignee and pushes it to the assignee on Telegram.

const KINDS = [
  { v: "FAULT", label: "خرابی", color: "red" },
  { v: "SUPPORT", label: "پشتیبانی", color: "blue" },
  { v: "INSTALL", label: "نصب و راه‌اندازی", color: "amber" },
  { v: "PROJECT", label: "پروژه", color: "dark" },
];
const KIND = Object.fromEntries(KINDS.map((k) => [k.v, k]));
const STATUS = {
  OPEN: { label: "باز", color: "amber" },
  IN_PROGRESS: { label: "در حال انجام", color: "blue" },
  DONE: { label: "انجام‌شده", color: "green" },
};
const MGMT = "mgmt"; // sentinel for "مدیریت" (no single assignee)

function ago(iso) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  const fa = (n) => n.toLocaleString("fa-IR");
  if (mins < 1) return "همین الان";
  if (mins < 60) return `${fa(mins)} دقیقه پیش`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${fa(h)} ساعت پیش`;
  return `${fa(Math.round(h / 24))} روز پیش`;
}

export default function Tasks() {
  const { user } = useAuth();
  const [people, setPeople] = useState([]);
  const [summary, setSummary] = useState({});
  const [tg, setTg] = useState(null);
  const [scope, setScope] = useState("mine");
  const [status, setStatus] = useState("active");
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [flash, setFlash] = useState(null);
  const [openId, setOpenId] = useState(null);

  function loadList() {
    setLoading(true);
    api.get(`/tasks?scope=${scope}&status=${status}`)
      .then((d) => setList(rows(d)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    api.get("/tasks/summary").then(setSummary).catch(() => {});
  }
  useEffect(() => { loadList(); }, [scope, status]); // eslint-disable-line
  useEffect(() => {
    api.get("/tasks/people").then(setPeople).catch(() => {});
    api.get("/telegram/status").then(setTg).catch(() => {});
  }, []);

  function replace(task) {
    setList((l) => l.map((t) => (t.id === task.id ? { ...t, ...task } : t)));
    api.get("/tasks/summary").then(setSummary).catch(() => {});
  }

  async function act(task, path, body) {
    setError(null);
    try { const t = await api.post(`/tasks/${task.id}/${path}`, body || {}); replace(t); return t; }
    catch (e) { setError(e.message); return null; }
  }

  function onCreated(task) {
    setFlash(`${task.number} ثبت شد و به «${task.assignee_name}» رسید.`);
    setTimeout(() => setFlash(null), 4000);
    loadList();
  }

  return (
    <div style={{ maxWidth: 980, margin: "0 auto" }}>
      <div className="toolbar" style={{ marginBottom: 12 }}>
        <div>
          <h1 className="page-title">کارها</h1>
          <div className="page-sub">هر خرابی، پشتیبانی، نصب یا پروژه‌ای که مشتری اعلام کرد را همین‌جا بنویسید.</div>
        </div>
        {tg?.enabled && !tg.linked && tg.link_url && (
          <a className="btn sm" href={tg.link_url} target="_blank" rel="noreferrer"
            title="یک بار وصل کنید تا کارهای شما در تلگرام بیاید">
            اتصال تلگرام من
          </a>
        )}
        {tg?.linked && <span className="badge green"><Icon name="check" size={13} /> تلگرام وصل است</span>}
      </div>

      <Composer people={people} me={user} onCreated={onCreated} />
      {flash && <div className="flash">{flash}</div>}
      {error && <div className="error">{error}</div>}

      <div className="flex" style={{ justifyContent: "space-between", margin: "20px 0 12px", flexWrap: "wrap" }}>
        <div className="seg" style={{ minWidth: 330 }}>
          <button className={scope === "mine" ? "active" : ""} onClick={() => setScope("mine")}>
            مال من {summary.mine_open > 0 && <span className="pill">{summary.mine_open.toLocaleString("fa-IR")}</span>}
          </button>
          <button className={scope === "sent" ? "active" : ""} onClick={() => setScope("sent")}>ارجاع داده‌ام</button>
          <button className={scope === "all" ? "active" : ""} onClick={() => setScope("all")}>همه</button>
        </div>
        <div className="seg">
          <button className={status === "active" ? "active" : ""} onClick={() => setStatus("active")}>در جریان</button>
          <button className={status === "DONE" ? "active" : ""} onClick={() => setStatus("DONE")}>انجام‌شده</button>
        </div>
      </div>

      {loading ? <div className="empty">در حال بارگذاری…</div> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {list.map((t) => (
            <TaskRow key={t.id} task={t} people={people} summary={summary}
              onAct={act} onOpen={() => setOpenId(t.id)} />
          ))}
          {list.length === 0 && (
            <div className="empty">{status === "DONE" ? "هنوز کاری انجام نشده." : "کار بازی نیست 🎉"}</div>
          )}
        </div>
      )}

      {openId && (
        <TaskDetail id={openId} people={people} summary={summary}
          onClose={() => { setOpenId(null); loadList(); }} onChanged={replace} />
      )}
    </div>
  );
}

// --- Composer: the single text box --------------------------------------------
function Composer({ people, me, onCreated }) {
  const [text, setText] = useState("");
  const [guess, setGuess] = useState(null);
  const [over, setOver] = useState({}); // user overrides: kind / assignee / customer
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const ref = useRef(null);
  const timer = useRef(null);

  useEffect(() => {
    clearTimeout(timer.current);
    if (!text.trim()) { setGuess(null); return; }
    timer.current = setTimeout(() => {
      api.post("/tasks/parse", { text }).then(setGuess).catch(() => {});
    }, 250);
    return () => clearTimeout(timer.current);
  }, [text]);

  // "@" mention suggestions for the word under the cursor.
  const mention = useMemo(() => {
    const m = text.match(/@([^\s@]*)$/);
    if (!m) return null;
    const q = m[1].replace(/_/g, " ");
    return people.filter((p) => p.full_name.includes(q)).slice(0, 6);
  }, [text, people]);

  function pickMention(p) {
    const first = p.full_name.split(" ")[0];
    const unique = people.filter((x) => x.full_name.split(" ")[0] === first).length === 1;
    const token = unique ? first : p.full_name.replace(/\s+/g, "_");
    setText(text.replace(/@([^\s@]*)$/, `@${token} `));
    setOver({ ...over, assignee: p.id });
    ref.current?.focus();
  }

  const kind = over.kind || guess?.kind || "SUPPORT";
  const assigneeId = "assignee" in over ? over.assignee : (guess?.mention_found ? (guess.assignee?.id ?? MGMT) : MGMT);
  const assigneeName = assigneeId === MGMT ? "مدیریت (سهیل و عماد)"
    : (people.find((p) => p.id === assigneeId)?.full_name || guess?.assignee?.full_name || "");
  const customer = "customer" in over ? over.customer
    : guess?.customer ? { id: guess.customer.id, name: guess.customer.name }
    : guess?.customer_name ? { id: null, name: guess.customer_name } : null;

  async function submit() {
    if (!text.trim() || busy) return;
    setBusy(true); setErr(null);
    try {
      const body = { text, kind, assignee: assigneeId === MGMT ? null : assigneeId };
      if (customer?.id) body.customer = customer.id;
      else { body.customer = null; body.customer_name = customer?.name || ""; }
      const t = await api.post("/tasks", body);
      setText(""); setOver({}); setGuess(null);
      onCreated(t);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); ref.current?.focus(); }
  }

  return (
    <div className="composer">
      <div style={{ position: "relative" }}>
        <textarea ref={ref} rows={2} value={text} autoFocus
          placeholder="مثلاً: شرکت آلفا سرورش از دیشب خاموشه @عماد"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (mention && mention.length) pickMention(mention[0]); else submit();
            }
          }} />
        {mention && mention.length > 0 && (
          <div className="menu" style={{ top: "100%", right: 0, left: "auto", marginTop: 4 }}>
            <div className="head">ارجاع به…</div>
            {mention.map((p) => (
              <button key={p.id} type="button" onMouseDown={(e) => { e.preventDefault(); pickMention(p); }}>
                <Avatar name={p.full_name} size={22} radius={7} /> {p.full_name}
                {p.id === me?.id && <span className="muted" style={{ fontSize: 11 }}>(خودم)</span>}
              </button>
            ))}
          </div>
        )}
      </div>
      {err && <div className="error" style={{ margin: "10px 0 0" }}>{err}</div>}
      <div className="chips">
        {text.trim() && <>
        <CustomerChip value={customer} onChange={(c) => setOver({ ...over, customer: c })} />
        <ChipSelect icon="doc" label="نوع" value={kind} onChange={(v) => setOver({ ...over, kind: v })}
          options={KINDS.map((k) => ({ v: k.v, label: k.label }))} />
        <ChipSelect icon="users" label="مسئول" value={assigneeId === MGMT ? MGMT : String(assigneeId)}
          display={assigneeName}
          onChange={(v) => setOver({ ...over, assignee: v === MGMT ? MGMT : Number(v) })}
          options={[{ v: MGMT, label: "مدیریت (سهیل و عماد)" },
            ...people.map((p) => ({ v: String(p.id), label: p.full_name + (p.telegram ? "" : " · بدون تلگرام") }))]} />
        </>}
        {!text.trim() && <span className="muted" style={{ fontSize: 12 }}>Enter = ثبت · با @ به همکار ارجاع بدهید · بدون @ به مدیریت می‌رسد</span>}
        <button className="btn primary" style={{ marginInlineStart: "auto" }} disabled={!text.trim() || busy} onClick={submit}>
          {busy ? "در حال ثبت…" : "ثبت ↵"}
        </button>
      </div>
    </div>
  );
}

function ChipSelect({ icon, label, value, display, options, onChange }) {
  const shown = display || options.find((o) => o.v === value)?.label || "—";
  return (
    <label className="chip" title={`تغییر ${label}`}>
      <Icon name={icon} size={14} />
      <span className="muted">{label}:</span> <b>{shown}</b>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
      </select>
    </label>
  );
}

function CustomerChip({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [res, setRes] = useState([]);
  const ref = useRef(null);
  useEffect(() => {
    function onDoc(e) { if (ref.current && !ref.current.contains(e.target)) setOpen(false); }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);
  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => {
      api.get(`/parties?role=customer&q=${encodeURIComponent(q)}`).then((d) => setRes(rows(d).slice(0, 8))).catch(() => {});
    }, 200);
    return () => clearTimeout(t);
  }, [q, open]);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button type="button" className={`chip ${value && !value.id ? "warn" : ""}`} onClick={() => { setOpen(!open); setQ(""); }}>
        <Icon name="users" size={14} />
        <span className="muted">مشتری:</span> <b>{value?.name || "—"}</b>
        {value && !value.id && <span style={{ fontSize: 11 }}>(جدید)</span>}
        {value?.id && <Icon name="check" size={13} color="#10a86b" />}
      </button>
      {open && (
        <div className="menu" style={{ top: "110%", right: 0, left: "auto", width: 260 }}>
          <input autoFocus placeholder="جستجوی مشتری…" value={q} onChange={(e) => setQ(e.target.value)}
            style={{ marginBottom: 6, padding: "7px 10px", fontSize: 13 }} />
          {res.map((p) => (
            <button key={p.id} type="button" onClick={() => { onChange({ id: p.id, name: p.name }); setOpen(false); }}>{p.name}</button>
          ))}
          {q.trim() && !res.some((p) => p.name === q.trim()) && (
            <button type="button" onClick={() => { onChange({ id: null, name: q.trim() }); setOpen(false); }}>
              <Icon name="plus" size={14} /> «{q.trim()}» (مشتری جدید)
            </button>
          )}
          <div className="sep" />
          <button type="button" onClick={() => { onChange(null); setOpen(false); }}>بدون مشتری</button>
        </div>
      )}
    </div>
  );
}

// --- One task row ---------------------------------------------------------------
function TaskRow({ task: t, people, summary, onAct, onOpen }) {
  const navigate = useNavigate();
  const k = KIND[t.kind] || KIND.SUPPORT;
  const s = STATUS[t.status];
  async function proforma() {
    const r = await api.post(`/tasks/${t.id}/proforma`).catch((e) => { alert(e.message); return null; });
    if (r) navigate(`/proformas?open=${r.proforma}`);
  }
  return (
    <div className={`task-row ${t.status === "DONE" ? "done" : ""}`}>
      <div style={{ flex: 1, minWidth: 0, cursor: "pointer" }} onClick={onOpen}>
        <div className="flex" style={{ flexWrap: "wrap", gap: 6 }}>
          <span className={`badge ${k.color}`}>{k.label}</span>
          <span className={`badge ${s.color}`}>{s.label}</span>
          <span className="muted num" style={{ fontSize: 12 }}>{t.number}</span>
          {t.customer_display && <b style={{ fontSize: 13.5 }}>{t.customer_display}</b>}
        </div>
        <div className="task-text">{t.text}</div>
        <div className="muted" style={{ fontSize: 12 }}>
          ثبت: {t.created_by_name} · {ago(t.created_at)}
          {t.proforma_number && <> · پیش‌فاکتور {t.proforma_number}</>}
        </div>
      </div>
      <div className="task-actions">
        <label className="chip" title="ارجاع به…">
          <Avatar name={t.assignee_name} size={22} radius={7} />
          <b>{t.assignee_name}</b>
          <select value={t.assignee ?? MGMT}
            onChange={(e) => onAct(t, "assign", { assignee: e.target.value === MGMT ? null : Number(e.target.value) })}>
            <option value={MGMT}>مدیریت</option>
            {people.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}
          </select>
        </label>
        {t.status === "OPEN" && <button className="btn sm" onClick={() => onAct(t, "status", { status: "IN_PROGRESS" })}>شروع کردم</button>}
        {t.status !== "DONE" && <button className="btn sm success" onClick={() => onAct(t, "status", { status: "DONE" })}>انجام شد ✓</button>}
        {t.status === "DONE" && summary.can_issue_proforma && !t.proforma && (
          <button className="btn sm primary" onClick={proforma}>صدور پیش‌فاکتور</button>
        )}
        {t.status === "DONE" && <button className="btn sm" onClick={() => onAct(t, "status", { status: "OPEN" })} title="بازگشایی">↺</button>}
      </div>
    </div>
  );
}

// --- Detail: timeline + note -------------------------------------------------------
function TaskDetail({ id, people, summary, onClose, onChanged }) {
  const navigate = useNavigate();
  const [t, setT] = useState(null);
  const [note, setNote] = useState("");
  const [err, setErr] = useState(null);
  useEffect(() => { api.get(`/tasks/${id}`).then(setT).catch((e) => setErr(e.message)); }, [id]);

  async function post(path, body) {
    setErr(null);
    try { const r = await api.post(`/tasks/${id}/${path}`, body || {}); const task = r.task || r; setT(task); onChanged(task); return r; }
    catch (e) { setErr(e.message); return null; }
  }

  if (!t) return <Modal title="کار" onClose={onClose}>{err ? <div className="error">{err}</div> : <div className="empty">…</div>}</Modal>;
  return (
    <Modal title={`${t.number} · ${t.kind_display}`} icon="doc" onClose={onClose} wide>
      {err && <div className="error">{err}</div>}
      <div style={{ fontSize: 15, lineHeight: 1.9, marginBottom: 12 }}>{t.text}</div>
      <div className="chips" style={{ marginTop: 0 }}>
        <span className={`badge ${STATUS[t.status].color}`}>{t.status_display}</span>
        <span className="chip"><span className="muted">مشتری:</span> <b>{t.customer_display || "—"}</b></span>
        {!t.customer && t.customer_name && (
          <button className="btn sm" onClick={() => post("customer", { create: true })}>
            <Icon name="plus" size={13} /> افزودن به مشتری‌ها
          </button>
        )}
        <ChipSelect icon="doc" label="نوع" value={t.kind} onChange={(v) => post("kind", { kind: v })}
          options={KINDS.map((k) => ({ v: k.v, label: k.label }))} />
        <ChipSelect icon="users" label="مسئول" value={t.assignee ? String(t.assignee) : MGMT}
          display={t.assignee_name}
          onChange={(v) => post("assign", { assignee: v === MGMT ? null : Number(v) })}
          options={[{ v: MGMT, label: "مدیریت" }, ...people.map((p) => ({ v: String(p.id), label: p.full_name }))]} />
        {t.proforma
          ? <button className="btn sm" onClick={() => navigate(`/proformas?open=${t.proforma}`)}>پیش‌فاکتور {t.proforma_number}</button>
          : summary.can_issue_proforma && (
            <button className="btn sm primary" onClick={async () => {
              const r = await post("proforma");
              if (r) navigate(`/proformas?open=${r.proforma}`);
            }}>صدور پیش‌فاکتور</button>
          )}
      </div>

      <div className="timeline">
        {t.events.map((e) => (
          <div key={e.id} className="ev">
            <div className="dot" />
            <div>
              <div style={{ fontSize: 13.5 }}>
                <b>{e.actor_name || "سیستم"}</b> · {e.kind === "NOTE" ? e.text : e.kind === "CREATED" ? "ثبت کرد" : e.text}
              </div>
              <div className="muted" style={{ fontSize: 11.5 }}>{jalali(e.created_at, true)}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex" style={{ marginTop: 14 }}>
        <input placeholder="یادداشت… (مثلاً: قطعه سفارش داده شد)" value={note}
          onChange={(e) => setNote(e.target.value)}
          onKeyDown={async (e) => { if (e.key === "Enter" && note.trim()) { if (await post("note", { text: note })) setNote(""); } }} />
        <button className="btn" disabled={!note.trim()} onClick={async () => { if (await post("note", { text: note })) setNote(""); }}>ثبت</button>
      </div>
      <div className="flex" style={{ marginTop: 14, justifyContent: "flex-end" }}>
        {t.status === "OPEN" && <button className="btn" onClick={() => post("status", { status: "IN_PROGRESS" })}>شروع کردم</button>}
        {t.status !== "DONE"
          ? <button className="btn success" onClick={() => post("status", { status: "DONE" })}>انجام شد ✓</button>
          : <button className="btn" onClick={() => post("status", { status: "OPEN" })}>بازگشایی</button>}
      </div>
    </Modal>
  );
}
