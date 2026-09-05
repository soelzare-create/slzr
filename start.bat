@echo off
REM ============================================================
REM  DaranX (داران ایکس) - one-click launcher for Windows
REM  Sets up the backend (Django) and frontend (React/Vite) on
REM  first run, then starts both servers and opens the browser.
REM ============================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"

REM --- pick a Python launcher (py preferred, else python) ---
where py >nul 2>nul && (set "PY=py") || (set "PY=python")

echo(
echo [DaranX] Preparing backend...
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo [DaranX] Creating Python virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [DaranX] ERROR: could not create the virtual environment. Is Python installed?
        pause
        exit /b 1
    )
)

echo [DaranX] Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt

if not exist ".env" (
    echo [DaranX] Creating .env from .env.example...
    copy /y .env.example .env >nul
)

echo [DaranX] Applying database migrations...
".venv\Scripts\python.exe" manage.py migrate --no-input

echo [DaranX] Seeding initial data (safe to run repeatedly)...
".venv\Scripts\python.exe" manage.py seed

echo(
echo [DaranX] Preparing frontend...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [DaranX] Installing frontend dependencies (first run, may take a while)...
    call npm install
)

echo(
echo [DaranX] Starting servers in two new windows...
start "DaranX Backend"  /d "%~dp0backend"  cmd /k ".venv\Scripts\python.exe manage.py runserver"
start "DaranX Frontend" /d "%~dp0frontend" cmd /k "npm run dev"

echo [DaranX] Waiting for the servers to come up...
timeout /t 6 >nul
start "" http://localhost:5173

echo(
echo ============================================================
echo  DaranX is starting.
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
