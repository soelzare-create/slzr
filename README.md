# داران ایکس — نرم‌افزار حسابداری و فاکتور

> «همه چیز سر جای خودش»

نرم‌افزار یکپارچه حسابداری و فاکتور برای شرکت داران ایکس (فاز ۱ — بدون ماژول انبار).
اسناد مالی به‌صورت **خودکار** از رویدادهای خرید و فروش تولید می‌شوند، نه دستی.

## معماری

- **بک‌اند:** Django + Django REST Framework (مونولیت ماژولار، هر بخش یک اپ).
- **دیتابیس:** PostgreSQL (پیش‌فرض توسعه: SQLite، بدون نیاز به راه‌اندازی).
- **فرانت‌اند:** React (Vite) با پشتیبانی کامل فارسی و RTL.
- **احراز هویت:** JWT + RBAC مجوز-محور دیتابیسی (نه سخت‌کد).

اپ‌ها: `core` (Party/Item/Notification/AuditLog)، `accounts` (User + RBAC)،
`accounting` (کدینگ حساب‌ها + سند دوطرفه)، `procurement` (خرید)،
`sales` (پیش‌فاکتور + ماشین وضعیت + فاکتور)، `technical` (خدمات/پشتیبانی)،
`management` (داشبورد). منطق کسب‌وکار در لایه `services.py`.

## اجرای سریع در ویندوز (یک‌کلیک)

اگر روی ویندوز هستید، لازم نیست دستورها را دستی بزنید: فایل **`start.bat`** را در ریشهٔ
پروژه دابل‌کلیک کنید. این فایل بار اول محیط پایتون و وابستگی‌ها را نصب، دیتابیس را
`migrate`/`seed`، و وابستگی‌های فرانت را نصب می‌کند؛ سپس هر دو سرور را در دو پنجرهٔ جدا
بالا می‌آورد و مرورگر را روی http://localhost:5173 باز می‌کند.
پیش‌نیاز: نصب **Python** و **Node.js (LTS)**. ورود: `09120000000` / `admin1234`.
برای توقف، آن دو پنجرهٔ سرور را ببندید.

## راه‌اندازی بک‌اند

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # ویندوز: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # مقادیر را تنظیم کنید (به‌ویژه SECRET_KEY)
python manage.py migrate            # ساخت جداول
python manage.py seed               # ماتریس دسترسی + نقش‌ها + کاربر مدیر + کدینگ حساب‌ها
python manage.py runserver          # http://localhost:8000
```

- ورود اولیه: شماره `09120000000` / رمز `admin1234` — **بعد از اولین ورود عوض کنید**.

### دیتابیس توسعه: PostgreSQL (توصیه‌شده)

SQLite برای شروعِ بدون‌دردسر خوب است، اما **قفل ردیف ندارد**؛ یعنی
`select_for_update()` (رقابت FCFS رزرو ۴۸ ساعته در `apps/sales`) روی آن بی‌اثر
است و قابل تست نیست. برای همین توسعه و تست را روی همان موتوری انجام دهید که در
تولید اجرا می‌شود:

```bash
docker compose -f docker-compose.dev.yml up -d          # PostgreSQL روی localhost:5432
export DATABASE_URL=postgresql+psycopg://daranx:daranx@localhost:5432/daranx
cd backend && python manage.py migrate && python manage.py seed
```

سوییچ کد لازم نیست؛ فقط `DATABASE_URL` را در `.env` بگذارید.

### job رزرو نرم ۴۸ ساعته

```bash
python manage.py release_reservations   # cron/Celery beat هر ۱۵ دقیقه
```

### تست و لینت

```bash
cd backend
pip install -r requirements-dev.txt
ruff check .                    # لینت (پیکربندی در backend/ruff.toml)
python manage.py makemigrations --check --dry-run   # همگام‌بودن مایگریشن‌ها
pytest -q --cov=apps            # تست‌ها + پوشش
```

### pre-commit (اختیاری ولی توصیه‌شده)

تا لینت پیش از هر کامیت محلی اجرا شود و مشکلات قبل از CI گرفته شوند:

```bash
pip install pre-commit        # در requirements-dev.txt هم هست
pre-commit install            # یک‌بار؛ سپس روی هر `git commit` اجرا می‌شود
pre-commit run --all-files    # اجرای دستی روی کل مخزن
```

پیکربندی در `.pre-commit-config.yaml` (ruff + چند بررسی پایه).

### CI

هر push و هر Pull Request به‌صورت خودکار در GitHub Actions اجرا می‌شود
(`.github/workflows/ci.yml`): لینت با ruff، بررسی همگامیِ مایگریشن‌ها، و
اجرای کل تست‌ها **روی PostgreSQL** (همان موتور تولید).

## راه‌اندازی فرانت‌اند

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (به بک‌اند روی 8000 پروکسی می‌شود)
```

## جریان کاری (فروش کالا)

```
پیش‌فاکتور (DRAFT) → تأیید (CONFIRMED, رزرو ۴۸ ساعته)
   → منتظر خرید (AWAITING_PURCHASE) → آماده فاکتور (READY) → فاکتور (INVOICED)
جانبی: ابطال (CANCELLED)، تأمین‌نشدنی (UNFULFILLABLE)
```

1. **بازرگانی** خرید را ثبت می‌کند → سند «موجودی کالا / پرداختنی» + اعلان «آماده فاکتور».
2. **فروش** پیش‌فاکتور می‌سازد؛ هر قلم به یک خرید مبدأ وصل می‌شود (یک‌به‌یک).
3. **تبدیل به فاکتور**: قانون ۵٪ روی هر قلم بررسی می‌شود (فروش ≥ خرید × ۱٫۰۵)؛ سپس
   سند فروش خودکار (دریافتنی/درآمد + بهای تمام‌شده/موجودی).
4. ابطال/مرجوعی → سند مالی معکوس. همه در `AuditLog`.

## کدینگ حساب‌ها

دارایی (۱۰۰۰): صندوق/بانک ۱۱۰۰، دریافتنی ۱۲۰۰، موجودی کالا ۱۳۰۰ · بدهی (۲۰۰۰):
پرداختنی ۲۱۰۰ · سرمایه ۳۰۰۰ · درآمد (۴۰۰۰): فروش ۴۱۰۰، خدمات ۴۲۰۰، پشتیبانی ۴۳۰۰ ·
هزینه (۵۰۰۰): بهای تمام‌شده ۵۱۰۰.

## دسترسی (RBAC)

شش بخش، هر بخش دو نقش (مدیر/کارمند). کارمند فقط داده‌ی خودش را می‌بیند
(فیلتر `owner=user` در سطح object-level). مدیر بخش: `*.view_all`. مدیریت: همه بخش‌ها.
حسابداری بین‌بخشی: همه فاکتورها فقط‌خواندنی. ادمین سیستم جدا (`is_system_admin`).
افزودن دسترسی = یک ردیف در `RolePermission`، بدون تغییر کد.

## ساختار پوشه‌ها

```
slzr/
├── CLAUDE.md            # راهنمای فاز فعلی (اسپک)
├── backend/
│   ├── daranx/          # پیکربندی پروژه + api_urls
│   └── apps/            # core, accounts, accounting, procurement, sales, technical, management
│   └── tests/           # تست‌های pytest (قانون ۵٪، ماشین وضعیت، RBAC، اسناد)
└── frontend/            # React + RTL (Vite)
```
