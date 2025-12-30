@echo off
setlocal

REM Opens two terminals: backend + frontend.

start "Ledger Backend" cmd /k "%~dp0start_backend.bat"
start "Ledger Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo Backend:  http://127.0.0.1:8000/health
echo Frontend: http://localhost:5173
echo.
pause
