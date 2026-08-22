@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo    DaranX  -  local web app launcher
echo ============================================
echo.

REM ---- prerequisite: Python ----
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found.
  echo         Install Python 3.11+ from https://python.org
  echo         and tick "Add python.exe to PATH" during install.
  echo.
  pause
  exit /b 1
)

REM ---- prerequisite: Node.js ----
where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js not found.
  echo         Install Node.js 18+ from https://nodejs.org
  echo.
  pause
  exit /b 1
)

REM ================= BACKEND =================
cd backend
if not exist ".venv" (
  echo [backend] creating virtual environment and installing dependencies...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip >nul
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
if not exist ".env" copy .env.example .env >nul
if not exist "daranx.db" (
  echo [backend] seeding initial admin account...
  python -m app.seed
)
cd ..

REM ================= FRONTEND =================
cd frontend
if not exist "node_modules" (
  echo [frontend] installing npm packages ^(first run may take a minute^)...
  call npm install
)
cd ..

REM ================= LAUNCH =================
echo.
echo [launch] starting backend  ^(http://localhost:8000^)
start "DaranX Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload"

echo [launch] starting frontend ^(http://localhost:5173^)
start "DaranX Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [launch] opening browser in a few seconds...
timeout /t 6 /nobreak >nul
start "" http://localhost:5173

echo.
echo ============================================
echo   DaranX is running.
echo   Web app : http://localhost:5173
echo   API docs: http://localhost:8000/docs
echo   Login   : 09120000000  /  admin1234
echo.
echo   To stop: close the two opened server windows.
echo ============================================
echo.
pause
