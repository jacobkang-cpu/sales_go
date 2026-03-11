@echo off
setlocal
cd /d "%~dp0"

if exist ".\dist\card_admin_server.exe" (
  start "" ".\dist\card_admin_server.exe"
) else (
  start "" python ".\blog.py"
)

timeout /t 2 >nul
start "" "http://127.0.0.1:8000/card/woojin_card.html?slug=woojin"
start "" "http://127.0.0.1:8000/admin.html?slug=woojin"
start "" "http://127.0.0.1:8000/dashboard.html?slug=woojin"

echo Opened card, admin, and dashboard in browser.
