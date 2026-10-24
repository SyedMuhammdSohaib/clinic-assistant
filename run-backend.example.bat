@echo off
rem Copy this file to run-backend.bat and fill in your own values.
rem run-backend.bat is in .gitignore, so your keys never reach GitHub.
title Clinic backend
cd /d "%~dp0backend" || (echo backend folder nahi mila & pause & exit /b 1)
set "VENV=%~dp0.venv"
call "%VENV%\Scripts\activate.bat" || (echo .venv nahi mila: %VENV% & pause & exit /b 1)

rem If the password has @ in it, write %%40 instead of @ (e.g. abc@1 becomes abc%%401).
set "DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@localhost/clinic"
set "DOCTOR_API_KEY=choose-a-long-random-key"
set "BOT_API_KEY=choose-another-long-random-key"
rem Optional. Free key: https://aistudio.google.com/apikey  (use demo data only on the free tier)
set "GEMINI_API_KEY="
rem Optional. Login codes by SMS from your Android phone (app: SMS Gateway for Android).
rem Leave empty to see the codes in this window instead.
set "SMS_GATEWAY_URL="
set "SMS_GATEWAY_USER="
set "SMS_GATEWAY_PASSWORD="
rem Optional. The doctor gets an SMS on this number when a red flag fires.
set "DOCTOR_ALERT_PHONE="
rem Optional. Added to the "doctor answered" SMS, once the parent app is online.
set "PARENT_APP_URL="

echo Agar SMS on nahi hai ya fail ho, parent login code isi window mein aayega.
uvicorn app.main:app --reload
