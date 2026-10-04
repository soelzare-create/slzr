---
name: merchandising
description: Domain knowledge, working method and DaranX branding for the «Merchandising» project (this repo, by DaranX). Use it whenever a task touches merchandising in any sense — designing or reviewing a store layout / floor plan (پلان و نقشهٔ چیدمان فروشگاه، مسیر مشتری، دپارتمان‌ها، صندوق)، field/retail execution (مرچندایزر، چیدمان، ویزیت، پلانوگرام، فیسینگ، سهم قفسه، OSA/OOS، POSM)، visual merchandising (ویترین، دیسپلی)، merchandise planning (سبد کالا، category management، open-to-buy، markup/margin، GMROI، sell-through)، goods-trading accounting (موجودی، بهای تمام‌شده، برگشت از خرید/فروش، trade spend) or billing merchandising services. Also use it for models, APIs, screens, KPIs, reports, proposals or any client-facing document of this project, even if «merchandising» never appears — it carries a plan-review checklist, KPI formulas, a Persian/English glossary, a data-model blueprint, codebase mapping and DaranX visual-identity rules.
---

# Merchandising — دانش دامنه و روش کار

این پروژه «**Merchandising**» نام دارد: نرم‌افزار یکپارچهٔ حسابداری، فاکتور و (از این به بعد)
مرچندایزینگ، ساخت **DaranX**. این اسکیل کمک می‌کند هر کار مرتبط با مرچندایزینگ را با زبان
درست، فرمول درست، در جای درست کد و با هویت بصری درست انجام دهی — «همه چیز سرِ جای درستش».

## ۱. اول بفهم کدام «مرچندایزینگ»

واژهٔ merchandising چند معنای رایج دارد. پیش از طراحی، درخواست را به یکی (یا چند) نگاشت
کن، چون مدل داده و شاخص‌ها کاملاً فرق می‌کنند:

| عدسی | نشانه‌ها در درخواست | بخوان |
|---|---|---|
| **چیدمان کل فروشگاه (پلان)** | نقشه/پلان فروشگاه، جای دپارتمان‌ها، مسیر مشتری، ورودی، صندوق، گوندولا، نقد یا مقایسهٔ طرح چیدمان | `references/store-layout.md` (+ `planning-and-category.md` §۵ برای تخصیص فضا) |
| **اجرای میدانی / خرده‌فروشی** | مرچندایزر، ویزیت، چیدمان، قفسه، فیسینگ، پلانوگرام، OSA، POSM، فروشگاه زنجیره‌ای، مسیر، عکس، ممیزی | `references/field-execution.md` + `references/kpis-and-formulas.md` |
| **مرچندایزینگ بصری** | ویترین، دیسپلی، سرقفسه، نور، مسیر مشتری | `references/field-execution.md` §۶ |
| **برنامه‌ریزی کالا و طبقهٔ کالا** | سبد کالا، OTB، خرید فصل، قیمت‌گذاری، تخفیف، sell-through، GMROI | `references/planning-and-category.md` + `references/kpis-and-formulas.md` |
| **حسابداری شرکت بازرگانی / صورتحساب خدمات** | موجودی، بهای تمام‌شده، برگشت از خرید/فروش، قرارداد برند، فاکتور ماهانه، هزینهٔ ورود کالا | `references/accounting-and-billing.md` |

اگر درخواست مبهم است **و** پاسخ، چیزی را که می‌سازی عوض می‌کند، یک سؤال کوتاه با همین
گزینه‌ها بپرس. در غیر این صورت با فرض معقول جلو برو و فرض را صریح بگو. برای بافت ایران
(پخش مویرگی، زنجیره‌ای‌ها، مالیات) `references/iran-market.md` و برای اصطلاحات
`references/glossary.md` را ببین.

## ۲. روش کار: شناخت ← طراحی ← اجرا ← پشتیبانی

1. **شناخت** — بازیگران (برند، آژانس، زنجیره، فروشگاه، مرچندایزر)، دانه‌بندی هر شاخص،
   صورت و مخرج، و اینکه داده از کجا می‌آید. بدون این، شاخص‌ها بعداً قابل‌اعتماد نیستند.
2. **طراحی** — مدل داده (طرح پیشنهادی در `field-execution.md` §۷)، سرویس‌ها، ردیف‌های
   RBAC، اثر مالی هر رویداد. طرح را قبل از کدنویسی سنگین به کاربر نشان بده.
3. **اجرا** — طبق قواعد `CLAUDE.md` (بخش ۴ همین فایل).
4. **پشتیبانی** — تست pytest، `AuditLog`، اعلان‌ها، و مستند به‌روز.

## ۳. نقشهٔ مخزن (چه چیزی همین حالا وجود دارد)

| مفهوم مرچندایزینگ | معادل فعلی در کد |
|---|---|
| SKU / کالا یا خدمت | `apps/core/models.py` → `Item` (`sku`, `unit`, `kind`) |
| برند، زنجیره، تأمین‌کننده | `core.Party` (`is_customer`/`is_supplier`، شناسهٔ ملی، شماره ثبت) |
| خرید کالا/POSM | `apps/procurement` → `Purchase`/`PurchaseLine`؛ پیوند به فاکتور فروش |
| فروش کالا | `apps/sales` → `Proforma` → `Invoice` (`GOODS`) |
| خدمت به‌ازای ویزیت / قرارداد ماهانه | `Invoice.Type.SERVICE` / `SUPPORT` (+ `period_start/end`) از `apps/technical` |
| رسید و سریال | `apps/warehouse` → `GoodsReceipt`/`ReceiptItem` |
| اسناد مالی خودکار | `apps/accounting/services.py` → `post_entry`, `reverse_entry` |
| یادآوری/هشدار | `core.Notification` + `core.services.notify` |
| ردپای تغییر | `core.AuditLog` + `core.services.log_action` |
| دسترسی | `apps/accounts` (ماتریس دیتابیسی) + `seed.py` (`DEPARTMENTS`) |

هنوز **وجود ندارد**: فروشگاه/شعبه، ویزیت، مسیر، مشاهدهٔ قفسه، پلانوگرام، POSM، قرارداد برند،
VAT، برگشت جزئی، موجودی دائمی. ساخت هرکدام = طراحی جدید (با کاربر تأیید کن).

## ۴. قواعد ساخت در این مخزن

این‌ها از `CLAUDE.md` می‌آیند و برای کارهای مرچندایزینگ هم صادق‌اند:

- اپ جدا با مالکیت مدل‌های خودش (پیشنهاد: `apps/merchandising`)؛ منطق در `services.py`.
- هر عملیات چندجدولی در `transaction.atomic()`؛ رقابت روی یک ردیف ← `select_for_update()`.
- هر تغییر وضعیت ← `log_action(...)`. اعلان‌ها بعد از بلوک اتمیک (خارج از مسیر بحرانی).
- «کارمند فقط کار خودش» با `owner=user` در سطح شیء؛ بخش/دسترسی جدید = ردیف در seed.
- اسناد مالی فقط خودکار از رویداد (ویزیت تأییدشده، پایان دورهٔ قرارداد، ثبت خرید).
- پول: `Decimal` و ریال (`decimal_places=0`)؛ نرخ‌ها، وزن‌ها، آستانه‌ها و SLA = داده، نه ثابت.
- رابط فارسی و RTL، تاریخ شمسی در UI؛ کد و کامنت انگلیسی.

## ۵. شاخص‌ها: درست حساب کن

- مشاهدهٔ خام ذخیره کن (SKU × فروشگاه × ویزیت)، درصد را هنگام گزارش بساز.
- درصدها را میانگین ساده نگیر؛ صورت‌ها و مخرج‌ها را جدا جمع کن.
- مارک‌آپ (روی بها) را با حاشیه (روی قیمت) قاطی نکن؛ در UI برچسب صریح بگذار.
- برای هر عدد در گزارش، تست یا پاسخ از ماشین‌حساب استفاده کن:

```bash
python .claude/skills/merchandising/scripts/merch_calc.py --help
python .claude/skills/merchandising/scripts/merch_calc.py markup-margin --cost 70 --price 100
python .claude/skills/merchandising/scripts/merch_calc.py osa --available 46 --checked 50
python .claude/skills/merchandising/scripts/merch_calc.py perfect-store \
    --component osa=92:40 --component pog=80:30 --component price=100:20 --component posm=50:10
```

دستورها: `markup-margin`, `price`, `imu`, `gmroi`, `sell-through`, `turnover`, `wos`, `otb`,
`sos`, `osa`, `compliance`, `perfect-store`, `visit-cost`, `selftest` (فرمول‌ها و دانه‌بندی:
`references/kpis-and-formulas.md`).

## ۶. برندینگ: هر خروجی با هویت DaranX

هر چیزی که آدم‌ها می‌بینند — گزارش ممیزی، گزارش ماهانهٔ برند، پروپوزال خدمات، صفحهٔ جدید
اپ، داشبورد، سند چاپی — با هویت بصری DaranX:

- برای سند HTML اسکیل `daranx-proposal-kit` را بارگذاری کن و از قالب آن شروع کن.
- نام‌ها: **DaranX** (X استیل)، «داران‌ایکس»، محصول «Merchandising — DaranX».
- رنگ‌ها نیوی/استیل از توکن‌ها، فونت Vazirmatn، روشن و تیره، RTL.
- عدد، مشتری، نمونه‌کار یا لوگوی ساختگی نیاور.

جزئیات، توکن‌ها و نگاشت پالت اپ به برند: `references/branding.md`. نمونهٔ کامل:
`docs/merchandising/research.html`.

## ۷. نقد یا طراحی پلان فروشگاه

وقتی نقشه/پلان می‌رسد: اول طبق `references/store-layout.md` §۱ نقشه را دقیق بخوان (برچسب‌های
ریز را برش و بزرگ کن، دستهٔ هر وجه گوندولا را جدول کن، مسیر مشتری را رسم کن)، بعد چک‌لیست §۳ را
برو، هر یافته را با کد، محل دقیق، شدت (§۴)، دلیل و اصلاح بنویس، و نقاط قوت را هم بگو. اگر گزارش
رسمی خواستند، ساختار §۵ را با قالب DaranX بساز.

## ۸. صداقت در دامنه

- ارقام بازار، تعرفهٔ زنجیره‌ها، نرخ قرارداد و حقوق نیرو را حدس نزن؛ بپرس یا جای خالی بگذار.
- نرخ مالیات و الزامات سامانهٔ مودیان سالانه عوض می‌شوند؛ قبل از استفاده بررسی کن.
- ادعاهای تبلیغاتی سایت‌های نرم‌افزاری را واقعیت فرض نکن.
- تصمیم‌های سیاستی (موجودی دائمی، طبقه‌بندی هزینهٔ ترید، کدینگ حساب جدید) با کاربر است؛
  گزینه‌ها و پیامدها را بگو، بی‌صدا عوض نکن.

## فهرست مراجع

| فایل | کی بخوانی |
|---|---|
| `references/glossary.md` | نام‌گذاری مدل/فیلد/برچسب UI، ترجمهٔ اصطلاح |
| `references/store-layout.md` | نقد یا طراحی پلان کل فروشگاه: اصول با منبع، چک‌لیست، مقیاس شدت، ساختار گزارش |
| `references/kpis-and-formulas.md` | هر شاخص، فرمول، دانه‌بندی، تله‌های تجمیع |
| `references/field-execution.md` | ویزیت، مسیر، پلانوگرام، POSM، بصری، طرح دادهٔ پیشنهادی |
| `references/planning-and-category.md` | سبد کالا، طبقهٔ کالا، OTB، قیمت و تخفیف، فضای قفسه |
| `references/accounting-and-billing.md` | سندهای فعلی مخزن، شرکت بازرگانی، صورتحساب خدمات، VAT |
| `references/iran-market.md` | کانال‌ها، پخش مویرگی، زنجیره‌ای‌ها، الزامات محلی |
| `references/branding.md` | هویت بصری DaranX، توکن‌ها، نگاشت پالت اپ |
| `references/sources.md` | منابع تحقیق |
