@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
  echo Hãy chạy cai_dat_windows.cmd trước.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" chay_ung_dung.py
if errorlevel 1 pause
