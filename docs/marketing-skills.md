# اسکیل‌های دیجیتال مارکتینگ

اسکیل‌های متن‌باز (لایسنس MIT) که برای پروموت محصول به این پروژه اضافه شده‌اند.
در سطح پروژه نصب‌اند؛ برای نصب در سطح اکانت (همهٔ پروژه‌ها) از دستورهای زیر استفاده کنید.

## ۱. Marketing Skills — Corey Haines

- مخزن: https://github.com/coreyhaines31/marketingskills
- در این پروژه: ۷ اسکیل در `.claude/skills/` (نسخهٔ commit `b9ba399`):
  `product-marketing`، `launch`، `copywriting`، `cro`، `content-strategy`، `cold-email`، `sales-enablement`

نصب در سطح اکانت (فقط همین ۷ اسکیل):

```bash
git clone --depth 1 https://github.com/coreyhaines31/marketingskills.git /tmp/marketingskills
mkdir -p ~/.claude/skills
for s in product-marketing launch copywriting cro content-strategy cold-email sales-enablement; do
  cp -r /tmp/marketingskills/skills/$s ~/.claude/skills/
done
```

یا کل مجموعه (۵۰ اسکیل) به‌صورت پلاگین:

```
/plugin marketplace add coreyhaines31/marketingskills
/plugin install marketing-skills@marketingskills
```

## ۲. LinkedIn Skills — Serge Bulaev

- مخزن: https://github.com/sergebulaev/linkedin-skills
- ۱۲ اسکیل لینکدین: نوشتن پست، کامنت، پاسخ، بهینه‌سازی پروفایل، تقویم محتوا، Humanizer و…
- بدون تأیید شما چیزی منتشر نمی‌کند. `APIFY_TOKEN` اختیاری است.

نصب در سطح اکانت:

```bash
claude plugin marketplace add sergebulaev/linkedin-skills --scope user
claude plugin install linkedin-skills@linkedin-skills --scope user
```

## ۳. Claude SEO — AgriciDaniel

- مخزن: https://github.com/AgriciDaniel/claude-seo
- سئوی فنی، محتوا، schema، سئوی محلی و بهینه‌سازی برای جست‌وجوی هوش مصنوعی؛ گزارش PDF/Excel
- بعد از نصب یک بار `/seo setup` را اجرا کنید (وابستگی‌های پایتون).
- هوک دارد: بعد از ویرایش فایل‌های `html/jsx/tsx/vue` فقط schema را بررسی می‌کند.

نصب در سطح اکانت:

```bash
claude plugin marketplace add AgriciDaniel/claude-seo --scope user
claude plugin install claude-seo@agricidaniel-claude-seo --scope user
```

## نکته‌ها

- اگر در سطح اکانت نصب کردید، برای جلوگیری از تکرار می‌توانید نسخهٔ پروژه را حذف کنید.
- پلاگین‌ها روی نسخهٔ مشخصی قفل نیستند و از آخرین نسخهٔ گیت‌هاب به‌روز می‌شوند.
- قدم اول: اسکیل `product-marketing` تا سند پایهٔ محصول (`.agents/product-marketing.md`) ساخته شود.
