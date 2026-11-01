@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not in PATH. Install it from python.org and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
python -m pip install -q -r requirements.txt
python find_product_photos.py %*
pause
