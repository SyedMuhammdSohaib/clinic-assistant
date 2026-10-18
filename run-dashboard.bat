@echo off
title Clinic dashboard
cd /d "%~dp0dashboard" || (echo dashboard folder nahi mila & pause & exit /b 1)
if not exist .env.local (echo dashboard\.env.local missing: copy .env.local.example and set DOCTOR_API_KEY & pause & exit /b 1)
npm run dev
