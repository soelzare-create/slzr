@echo off
REM ============================================================
REM  Merchandising (DaranX) - one-click launcher for Windows
REM  Sets up the backend (Django) and frontend (React/Vite) on
REM  first run, then starts both servers and opens the browser.
REM ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

REM --- pick a Python launcher (py preferred, else python) ---
where py >nul 2>nul && (set "PY=py") || (set "PY=python")

echo(
echo [Merchandising] Preparing backend...
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [Merchandising] Creating Python virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [Merchandising] ERROR: could not create the virtual environment. Is Python installed?
        pause
        exit /b 1
    )
)

echo [Merchandising] Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt

if not exist ".env" (
    echo [Merchandising] Creating .env from .env.example...
    copy /y .env.example .env >nul
)

echo [Merchandising] Applying database migrations...
".venv\Scripts\python.exe" manage.py migrate --no-input

echo [Merchandising] Seeding initial data (safe to run repeatedly)...
".venv\Scripts\python.exe" manage.py seed

echo(
echo [Merchandising] Preparing frontend...
cd /d "%~dp0frontend"
REM Always install: after a git pull the dependencies in package.json may have
REM changed, and a stale node_modules (e.g. left from an older stack) makes the
REM dev server crash on start. npm is fast when everything is already up to date.
echo [Merchandising] Installing/updating frontend dependencies...
call npm install
if errorlevel 1 (
    echo [Merchandising] ERROR: npm install failed. Check your internet connection and that Node.js is installed.
    pause
    exit /b 1
)

echo(
echo [Merchandising] Starting servers in two new windows...
start "Merchandising Backend"  /d "%~dp0backend"  cmd /k ".venv\Scripts\python.exe manage.py runserver"
start "Merchandising Frontend" /d "%~dp0frontend" cmd /k "npm run dev"

echo [Merchandising] Waiting for the servers to come up...
timeout /t 6 >nul
start "" http://localhost:5173

echo(
echo ============================================================
echo  Merchandising is starting.
echo    Frontend : http://localhost:5173   (open this in browser)
echo    Backend  : http://localhost:8000
echo    Login    : 09120000000  /  admin1234
echo(
echo  Two server windows opened. Keep them open while working.
echo  To stop the app, close those two windows.
echo ============================================================
echo(
echo This window can be closed.
pause
endlocal
