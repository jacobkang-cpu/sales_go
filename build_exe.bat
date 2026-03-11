@echo off
setlocal
cd /d "%~dp0"

where pyinstaller >nul 2>nul
if errorlevel 1 (
  echo [ERROR] pyinstaller is not installed.
  echo Run this first:
  echo   python -m pip install pyinstaller
  exit /b 1
)

echo [INFO] Building card admin server EXE...
pyinstaller --onefile --name card_admin_server blog.py
if errorlevel 1 (
  echo [ERROR] Build failed.
  exit /b 1
)

echo [DONE] dist\card_admin_server.exe
echo [TIP] Run start_card_admin.bat to open card/admin/dashboard.
