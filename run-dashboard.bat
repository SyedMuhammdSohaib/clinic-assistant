@echo off
title Clinic dashboard
cd /d "%~dp0dashboard" || (echo dashboard folder nahi mila & pause & exit /b 1)
if not exist .env.local (echo dashboard\.env.local missing: copy .env.local.example and set DOCTOR_API_KEY & pause & exit /b 1)
if not exist node_modules\.bin\next.cmd (
  echo Dashboard ke packages install ho rahe hain, 2-5 minute lagenge...
  call npm install --no-fund --no-audit || (echo npm install fail ho gaya & pause & exit /b 1)
)
call npm run dev
echo.
echo Dashboard band ho gaya. Upar error dekhein.
pause
