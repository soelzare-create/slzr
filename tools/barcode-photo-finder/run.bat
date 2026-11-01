@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag your Excel file onto this run.bat, or: run.bat products.xlsx
  pause
  exit /b 1
)
python -m pip install -q -r requirements.txt
python find_product_photos.py %*
pause
