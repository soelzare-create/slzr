# استقرار بک‌اند داران ایکس (Deployment)

راهنمای استقرارِ بک‌اند Django روی محیط واقعی. استک تولید:
**gunicorn** (اپلیکیشن‌سرور) + **PostgreSQL** (دیتابیس) + **WhiteNoise** (فایل‌های
استاتیک ادمین/DRF) + **Docker**. همه‌چیز از طریق متغیرهای محیطی تنظیم می‌شود؛ بدون
تغییر کد به PostgreSQL می‌رود.

> فلسفه: «همه چیز سر جای درستش». این فایل‌ها بستر استقرار را آماده می‌کنند؛ اجرای
> واقعی روی سرور شما و با اطلاعات شما انجام می‌شود.

## پیش از هر چیز: کلید و رمز

```bash
# یک SECRET_KEY امن بسازید:
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
فایل نمونه را کپی و مقداردهی کنید (این فایلِ پرشده هرگز commit نشود):
```bash
cp backend/.env.production.example backend/.env
# سپس مقادیر را ویرایش کنید: SECRET_KEY، ALLOWED_HOSTS، DATABASE_URL، رمز ادمین ...
```

---

## گزینهٔ A — یک سرور (VPS) با Docker Compose (ساده‌ترین)

پیش‌نیاز: Docker و Docker Compose روی سرور.

```bash
# 1) فایل env را بسازید و ویرایش کنید
cp backend/.env.production.example backend/.env
#    - DEBUG=false
#    - ALLOWED_HOSTS=دامنه شما (مثلاً api.daranx.com)
#    - DATABASE_URL=postgresql+psycopg://daranx:PASSWORD@db:5432/daranx
#    - رمز داخل DATABASE_URL باید با POSTGRES_PASSWORD یکی باشد

# 2) رمز دیتابیس را هم‌زمان برای سرویس db ست کنید (یا در .env کنار compose)
export POSTGRES_PASSWORD='یک-رمز-قوی'

# 3) بالا آوردن (build + migrate + seed خودکار در اولین اجرا)
docker compose up -d --build

# 4) بررسی سلامت
curl http://SERVER_IP:8000/health      # → {"status":"ok"}
docker compose logs -f web
```

سرویس‌های compose:
- **web** — gunicorn روی پورت ۸۰۰۰ (در اولین بوت خودش `migrate` و `seed` می‌کند).
- **db** — PostgreSQL 16 با volume ماندگار (`db_data`).
- **reservations** — هر ۱۵ دقیقه `release_reservations` را اجرا می‌کند (آزادسازی
  رزروِ نرمِ ۴۸ ساعته، بخش ۵ اسپک).

پس از اولین بوتِ موفق، در `backend/.env` مقدار `SEED_ON_START=false` را بگذارید تا
مرحلهٔ seed دوباره اجرا نشود (idempotent است، ولی لازم نیست).

### TLS / دامنه (توصیه‌شده)
پورت ۸۰۰۰ را مستقیم روی اینترنت باز نگذارید؛ یک reverse proxy با HTTPS جلوی آن بگذارید.
نمونهٔ Caddy (خودکار گواهی می‌گیرد):
```
api.daranx.com {
    reverse_proxy 127.0.0.1:8000
}
```
سپس در `backend/.env`:
```
CSRF_TRUSTED_ORIGINS=https://api.daranx.com
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
```
بک‌اند هدرِ `X-Forwarded-Proto` را از پراکسی می‌خواند (در تنظیمات لحاظ شده).

---

## گزینهٔ B — سکوهای ابری (PaaS)

هر سکویی که از **Dockerfile** یا Django/Python پشتیبانی کند کار می‌کند
(مثلاً Liara، Render، Railway، Fly.io). دو نکته:

1. یک دیتابیس **PostgreSQL** مدیریت‌شده بسازید و رشتهٔ اتصال آن را به شکل زیر در
   `DATABASE_URL` بگذارید (پیشوند `postgresql+psycopg://`):
   ```
   DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/DBNAME
   ```
2. متغیرهای محیطی جدول زیر را ست کنید. اگر سکو از Dockerfile استفاده کند، تصویر
   خودش `collectstatic` را در build و `migrate`+`seed` را در بوت انجام می‌دهد.
   اگر سکو مستقیماً Python را اجرا می‌کند، دستور اجرا این باشد:
   ```
   gunicorn daranx.wsgi:application --bind 0.0.0.0:$PORT
   ```
   و پیش از آن یک‌بار: `python manage.py migrate && python manage.py seed`.

برای آزادسازی رزرو ۴۸ ساعته، یک **Cron/Scheduled job** هر ۱۵ دقیقه بسازید که
`python manage.py release_reservations` را اجرا کند.

---

## متغیرهای محیطی

| متغیر | نمونه | توضیح |
|---|---|---|
| `SECRET_KEY` | `token_urlsafe(64)` | **الزامی** در تولید |
| `DEBUG` | `false` | در تولید حتماً false |
| `ALLOWED_HOSTS` | `api.daranx.com` | دامنه‌ها با کاما |
| `CSRF_TRUSTED_ORIGINS` | `https://api.daranx.com` | با scheme |
| `DATABASE_URL` | `postgresql+psycopg://...` | خالی = SQLite (فقط توسعه) |
| `CORS_ORIGINS` | `https://app.daranx.com` | مبدأ فرانت‌اند |
| `ACCESS_MINUTES` | `480` | عمر توکن JWT |
| `SECURE_SSL_REDIRECT` | `true` | بعد از فعال‌شدن TLS |
| `SECURE_HSTS_SECONDS` | `31536000` | بعد از اطمینان از TLS |
| `FIRST_ADMIN_PHONE` | `09120000000` | ادمین اولیه (seed) |
| `FIRST_ADMIN_PASSWORD` | — | **بعد از اولین ورود عوض کنید** |
| `SEED_ON_START` | `true`→`false` | بعد از اولین بوت false |
| `WEB_CONCURRENCY` | `3` | تعداد workerهای gunicorn |

---

## بعد از استقرار (چک‌لیست)

- [ ] `GET /health` → `{"status":"ok"}`
- [ ] ورود: `POST /api/auth/login` با `FIRST_ADMIN_PHONE` و رمز → توکن JWT برمی‌گردد
- [ ] ورود به پنل و **تغییر فوری رمز ادمین**
- [ ] `SEED_ON_START=false` تنظیم شد
- [ ] TLS فعال و `SECURE_SSL_REDIRECT=true`
- [ ] job رزرو (`release_reservations`) در حال اجراست
- [ ] `CORS_ORIGINS` روی دامنهٔ واقعی فرانت‌اند تنظیم شد

---

## فرانت‌اند (خلاصه)
فرانت (Vite/React) جدا build و روی هاست استاتیک/CDN مستقر می‌شود. آدرس API را به
دامنهٔ بک‌اند بدهید و همان دامنهٔ فرانت را در `CORS_ORIGINS` بک‌اند اضافه کنید.

## عیب‌یابی سریع
- **DisallowedHost** → دامنه در `ALLOWED_HOSTS` نیست.
- **CSRF/403 در ادمین** → دامنهٔ HTTPS را در `CSRF_TRUSTED_ORIGINS` بگذارید.
- **استاتیک ادمین ۴۰۴** → در تولید `collectstatic` لازم است (در Docker خودکار است).
- **اتصال دیتابیس** → پیشوند `postgresql+psycopg://` و درست‌بودن host/port/رمز.
