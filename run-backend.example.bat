@echo off
rem Copy this file to run-backend.bat and fill in your own values.
rem run-backend.bat is in .gitignore, so your keys never reach GitHub.
title Clinic backend
cd /d "%~dp0backend" || (echo backend folder nahi mila & pause & exit /b 1)
set "VENV=%~dp0.venv"
call "%VENV%\Scripts\activate.bat" || (echo .venv nahi mila: %VENV% & pause & exit /b 1)

set "DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@localhost/clinic"
set "DOCTOR_API_KEY=choose-a-long-random-key"
set "BOT_API_KEY=choose-another-long-random-key"
rem Optional. Free key: https://aistudio.google.com/apikey  (use demo data only on the free tier)
set "GEMINI_API_KEY="

echo Parent login codes will appear in this window.
uvicorn app.main:app --reload
