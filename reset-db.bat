@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo    DaranX  -  reset database (clean slate)
echo ============================================
echo.
echo این کار دیتابیس فعلی را پاک می‌کند و از نو می‌سازد.
echo همه‌ی اطلاعات ثبت‌شده حذف می‌شود.
echo.
set /p ok=برای ادامه Y را بزنید (هر چیز دیگر = انصراف):
if /I not "%ok%"=="Y" (
  echo لغو شد.
  pause
  exit /b 0
)

cd backend
if not exist ".venv" (
  echo [ERROR] ابتدا یک‌بار start.bat را اجرا کنید تا محیط ساخته شود.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat

if exist "daranx.db" del "daranx.db"
echo [db] ساخت دیتابیس تازه و حساب مدیر...
python -m app.seed

echo.
echo انجام شد. حالا می‌توانید start.bat را بزنید.
echo ورود: 09120000000 / admin1234
echo.
pause
