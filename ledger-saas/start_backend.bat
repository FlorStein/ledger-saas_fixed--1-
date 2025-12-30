@echo off
setlocal

cd /d "%~dp0backend"

if not exist ".env" (
  copy ".env.example" ".env" >nul
)

if not exist ".venv" (
  py -3.12 -m venv .venv
)

call .venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
