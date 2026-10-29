@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Chưa tìm thấy Python. Hãy cài Python 64-bit từ python.org, bật tùy chọn Add Python to PATH.
    pause
    exit /b 1
  )
  python -m venv .venv
) else (
  py -3 -m venv .venv
)
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" scripts\kiem_tra_moi_truong.py
if errorlevel 1 goto :failed
echo.
echo Cài đặt hoàn tất. Mở chay_windows.cmd để bắt đầu.
pause
exit /b 0
:failed
echo.
echo Cài đặt chưa thành công. Kiểm tra Internet và Python 64-bit, xem HUONG_DAN_WINDOWS.md.
pause
exit /b 1
