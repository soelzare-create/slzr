import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, toman, jalali } from "../api";

// Company letterhead constants (DaranX brand).
const CO = {
  name: "Daran X",
  sub: "شرکت فناوری اطلاعات داران",
  addr1: "تهران، میدان فاطمی، نبش خ چهل‌ستون،",
  addr2: "ساختمان چهل‌ستون، پلاک ۲ طبقه ۲ واحد ۲۰۲",
  phones: ["۰۲۱ ۸۸ ۹۶ ۴۱ ۱۶", "۰۲۱ ۸۸ ۹۶ ۶۹ ۰۴"],
  mobile: "۰۹۳۵ ۹۳۷ ۰۹ ۱۰",
};

const TITLES = { invoice: "فاکتور فروش", proforma: "پیش‌فاکتور", delivery: "حواله تحویل کالا" };

export default function DocumentPrint() {
  const { kind, id } = useParams(); // kind: invoice | proforma | delivery
  const [doc, setDoc] = useState(null);
  const [party, setParty] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const path = kind === "proforma" ? `/proformas/${id}` : `/invoices/${id}`;
    api.get(path)
      .then((d) => {
        setDoc(d);
        if (d.customer) api.get(`/parties/${d.customer}`).then(setParty).catch(() => {});
      })
      .catch((e) => setError(e.message));
  }, [kind, id]);

  if (error) return <div style={{ padding: 40 }} className="error">{error}</div>;
  if (!doc) return <div style={{ padding: 40 }}>در حال بارگذاری…</div>;

  const isDelivery = kind === "delivery";
  const isProforma = kind === "proforma";
  const lines = doc.lines || [];

  // Delivery: one row per serial (fall back to a quantity row when no serials).
  const deliveryRows = [];
  if (isDelivery) {
    lines.forEach((l) => {
      const serials = l.serials || [];
      if (serials.length) serials.forEach((s) => deliveryRows.push({ name: l.item_name, qty: 1, serial: s }));
      else deliveryRows.push({ name: l.item_name, qty: l.quantity, serial: "" });
    });
    while (deliveryRows.length < 12) deliveryRows.push({ name: "", qty: "", serial: "" });
  }

  const faNum = (n) => Number(n).toLocaleString("fa-IR");

  return (
    <div className="print-root">
      <style>{CSS}</style>

      <div className="toolbar no-print">
        <button onClick={() => window.print()}>چاپ / خروجی PDF</button>
        <span>برای ذخیره به‌صورت PDF، در پنجرهٔ چاپ «Save as PDF» را انتخاب کنید.</span>
      </div>

      <div className="sheet">
        <Waves />
        <header className="head">
          <div className="brand">
            <Logo />
            <div>
              <div className="brand-name">{CO.name}</div>
              <div className="brand-sub">{CO.sub}</div>
            </div>
          </div>
          <h1 className="doc-title">{TITLES[kind]}</h1>
          <div className="contact">
            <div>{CO.addr1}</div>
            <div>{CO.addr2}</div>
            <div className="phones">{CO.phones.join("  ")}</div>
            <div className="phones">{CO.mobile}</div>
          </div>
        </header>

        <div className="meta">
          <div>تاریخ صدور: <b>{jalali(doc.date || doc.created_at)}</b></div>
          <div>{isProforma ? "شماره پیش‌فاکتور" : "شماره فاکتور"}: <b>{doc.number}</b></div>
        </div>

        {/* customer info */}
        <div className="cust">
          <div className="cust-badge">اطلاعات مشتری</div>
          <div className="cust-grid">
            <Field label="نام شرکت / شخص" value={party?.name || doc.customer_name} />
            <Field label="شماره تماس" value={party?.phone} />
            <Field label="آدرس" value={party?.address} wide={isDelivery} />
            {!isDelivery && <Field label="کد اقتصادی / شناسه ملی" value={party?.national_id} />}
            {!isDelivery && <Field label="پست الکترونیک" value={party?.email} />}
          </div>
        </div>

        {/* line items */}
        {isDelivery ? (
          <table className="items">
            <thead><tr><th className="c-row">ردیف</th><th>شرح کالا / خدمات</th><th className="c-qty">تعداد</th><th className="c-serial">سریال نامبر</th></tr></thead>
            <tbody>
              {deliveryRows.map((r, i) => (
                <tr key={i}>
                  <td className="c-row">{r.name ? faNum(i + 1) : ""}</td>
                  <td className="r">{r.name}</td>
                  <td className="c-qty">{r.qty !== "" ? faNum(r.qty) : ""}</td>
                  <td className="c-serial" dir="ltr">{r.serial}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="items">
            <thead><tr><th className="c-row">ردیف</th><th>شرح کالا / خدمات</th><th className="c-qty">تعداد</th><th className="c-price">قیمت واحد</th><th className="c-total">مبلغ کل</th></tr></thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={l.id}>
                  <td className="c-row">{faNum(i + 1)}</td>
                  <td className="r">{l.item_name}{l.description ? ` — ${l.description}` : ""}</td>
                  <td className="c-qty">{faNum(l.quantity)}</td>
                  <td className="c-price">{faNum(l.unit_price)}</td>
                  <td className="c-total">{faNum(Number(l.quantity) * Number(l.unit_price))}</td>
                </tr>
              ))}
              <tr className="sum">
                <td className="sum-label" colSpan={4}>جمع کل</td>
                <td className="c-total">{faNum(doc.total)}</td>
              </tr>
            </tbody>
          </table>
        )}

        {/* footers per doc */}
        {isProforma && (
          <>
            <div className="terms">
              <div className="terms-badge">توضیحات و شرایط</div>
              <ul>
                <li>این پیش‌فاکتور تنها جهت اطلاع صادر شده و فاقد ارزش مالی و تعهد قانونی می‌باشد.</li>
                <li>قیمت‌ها به ریال بوده و شامل مالیات بر ارزش افزوده می‌گردد.</li>
                <li>مدت اعتبار پیش‌فاکتور از تاریخ صدور درج‌شده در سربرگ می‌باشد.</li>
                <li>در صورت تغییر قیمت‌ها، پیش‌فاکتور مجدداً صادر خواهد شد.</li>
                <li>پرداخت از طریق حساب‌های رسمی شرکت انجام شود.</li>
              </ul>
            </div>
            <div className="bank">
              <b>اطلاعات حساب شرکت</b>
              <div>بانک ملت – شعبه فاطمی</div>
              <div>شماره حساب: ……………… شماره شبا: ……………… کد شعبه: …………</div>
            </div>
          </>
        )}

        {isDelivery && (
          <div className="declare">
            <div className="terms-badge">اظهارات تحویل‌گیرنده</div>
            <p><b>کالاها را طبق لیست فوق دریافت نمودم. اقلام از نظر تعداد، مدل، سریال و ظاهر فیزیکی بررسی و تطبیق داده شد.</b></p>
            <div className="checks">
              <div>☐ هیچ‌گونه ایراد ظاهری مشاهده نشد.</div>
              <div>☐ تست اولیه انجام شد و دستگاه بدون مشکل بود.</div>
              <div>☐ ایرادات زیر مشاهده شد.</div>
              <div>☐ تست اولیه انجام نشد (به دلیل عدم وجود برق/ امکانات/ زمان).</div>
            </div>
            <div className="recv">
              <div>نام و نام خانوادگی تحویل‌گیرنده: ………………………………</div>
              <div>امضاء و اثر انگشت: ………………………………</div>
              <div>تاریخ: …………………</div>
            </div>
          </div>
        )}

        {!isDelivery && (
          <div className="signs">
            <div>مُهر و امضاء<br />شرکت داران</div>
            <div>مُهر و امضاء<br />خریدار</div>
          </div>
        )}

        <FooterWave />
      </div>
    </div>
  );
}

function Field({ label, value, wide }) {
  return (
    <div className={`fld ${wide ? "wide" : ""}`}>
      <span className="lbl">{label}:</span>
      <span className="val">{value || "…………………………………"}</span>
    </div>
  );
}

function Logo() {
  return (
    <svg width="52" height="46" viewBox="0 0 52 46" fill="none" aria-hidden>
      <path d="M6 4 L26 23 L6 42" stroke="#12305a" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M46 4 L26 23 L46 42" stroke="#2f6bff" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Waves() {
  return (
    <svg className="wave-top" viewBox="0 0 600 150" preserveAspectRatio="none" aria-hidden>
      <path d="M600 0 H250 C360 40 330 120 200 150 H600 Z" fill="#12305a" opacity="0.16" />
      <path d="M600 0 H300 C400 50 370 130 250 155 H600 Z" fill="#9cc3e6" opacity="0.30" />
    </svg>
  );
}
function FooterWave() {
  return (
    <svg className="wave-bottom" viewBox="0 0 600 90" preserveAspectRatio="none" aria-hidden>
      <path d="M0 90 H600 V35 C470 5 360 70 230 55 C150 45 70 55 0 80 Z" fill="#9cc3e6" opacity="0.5" />
      <path d="M0 90 H600 V55 C470 30 360 85 230 72 C150 63 70 74 0 90 Z" fill="#12305a" opacity="0.9" />
    </svg>
  );
}

const CSS = `
.print-root { background:#e9edf3; min-height:100vh; padding:16px; }
.print-root * { box-sizing:border-box; }
.toolbar { max-width:210mm; margin:0 auto 12px; display:flex; gap:12px; align-items:center;
  background:#fff; border:1px solid #dce1ea; border-radius:10px; padding:10px 14px; font-size:13px; color:#556; }
.toolbar button { background:linear-gradient(135deg,#2f6bff,#12305a); color:#fff; border:none;
  border-radius:8px; padding:9px 18px; font-size:14px; font-family:inherit; cursor:pointer; }
.sheet { position:relative; width:210mm; min-height:297mm; margin:0 auto; background:#fff;
  padding:20mm 15mm 24mm; box-shadow:0 6px 24px rgba(16,32,58,.15); overflow:hidden; color:#10151f; }
.wave-top { position:absolute; top:0; right:0; width:62%; height:150px; z-index:0; }
.wave-bottom { position:absolute; bottom:0; left:0; width:100%; height:90px; z-index:0; }
.head { position:relative; z-index:2; display:flex; flex-direction:row-reverse; justify-content:space-between; align-items:flex-start; }
.brand { display:flex; gap:10px; align-items:center; }
.brand-name { font-size:22px; font-weight:800; letter-spacing:1px; color:#12305a; }
.brand-sub { font-size:11px; color:#334; }
.doc-title { position:absolute; top:26px; left:50%; transform:translateX(-50%); margin:0;
  font-size:26px; font-weight:800; color:#2f7fd0; }
.contact { text-align:right; font-size:11px; font-weight:700; color:#233; line-height:1.9; }
.contact .phones { direction:ltr; text-align:right; }
.meta { position:relative; z-index:2; margin-top:14px; font-size:12px; color:#334; line-height:2; }
.cust { position:relative; z-index:2; margin-top:14px; border:1px solid #e3e7f0; border-radius:12px; padding:16px; background:#fafbfe; }
.cust-badge { position:absolute; top:-13px; right:16px; background:#c9d6e6; color:#12305a;
  font-weight:800; font-size:13px; padding:4px 16px; border-radius:8px; }
.cust-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 26px; margin-top:6px; }
.fld { font-size:12.5px; display:flex; gap:6px; }
.fld.wide { grid-column:1 / -1; }
.fld .lbl { color:#12305a; font-weight:700; white-space:nowrap; }
.fld .val { flex:1; border-bottom:1px dotted #b9c2d0; color:#222; }
.items { width:100%; border-collapse:collapse; margin-top:20px; position:relative; z-index:2; }
.items th { background:#1c3a5e; color:#fff; font-size:13px; font-weight:700; padding:11px 8px; }
.items td { border:1px solid #d7deea; padding:9px 8px; font-size:12.5px; text-align:center; height:30px; }
.items td.r { text-align:right; }
.c-row { width:44px; } .c-qty { width:70px; } .c-price,.c-total { width:120px; } .c-serial { width:150px; }
.items .sum td { border:none; }
.items .sum .sum-label { background:#1c3a5e; color:#fff; font-weight:800; text-align:center; border-radius:0 0 4px 4px; }
.items .sum .c-total { font-weight:800; font-size:14px; }
.terms { position:relative; z-index:2; margin-top:22px; border:1px solid #e3e7f0; border-radius:12px; padding:16px 18px; }
.terms-badge, .declare .terms-badge { position:absolute; top:-13px; right:16px; background:#12305a; color:#fff;
  font-weight:800; font-size:13px; padding:4px 16px; border-radius:8px; }
.terms ul { margin:6px 18px 0; padding:0; }
.terms li { font-size:12px; color:#334; line-height:2; }
.bank { position:relative; z-index:2; margin-top:16px; font-size:12.5px; line-height:2; color:#223; }
.declare { position:relative; z-index:2; margin-top:22px; border:1px solid #e3e7f0; border-radius:12px; padding:16px 18px; }
.declare p { font-size:12.5px; margin:6px 0 10px; }
.checks { display:grid; grid-template-columns:1fr 1fr; gap:6px 18px; font-size:12px; color:#223; }
.recv { margin-top:16px; font-size:12.5px; line-height:2.4; }
.signs { position:relative; z-index:2; display:flex; justify-content:space-between; margin-top:40px; padding:0 30px;
  text-align:center; font-size:12.5px; font-weight:700; color:#223; line-height:1.8; }
@page { size:A4; margin:0; }
@media print {
  .print-root { background:#fff; padding:0; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .no-print { display:none !important; }
  .sheet { box-shadow:none; width:auto; min-height:auto; margin:0; }
}
`;
