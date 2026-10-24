@echo off
rem Runs the dashboard in production mode: built once, then fast and stable.
rem It is rebuilt only when the code changed (after a git pull). For editing the
rem dashboard's code with live reload, run "npm run dev" in the dashboard folder instead.
title Clinic dashboard
cd /d "%~dp0dashboard" || (echo dashboard folder nahi mila & pause & exit /b 1)
if not exist .env.local (echo dashboard\.env.local missing: copy .env.local.example and set DOCTOR_API_KEY & pause & exit /b 1)
if not exist node_modules\.bin\next.cmd (
  echo Dashboard ke packages install ho rahe hain, 2-5 minute lagenge...
  call npm install --no-fund --no-audit || (echo npm install fail ho gaya & pause & exit /b 1)
)

rem Which code is this? Rebuild when it differs from the last build, or there is no build yet.
set "CODE=unknown"
for /f %%h in ('git rev-parse HEAD 2^>nul') do set "CODE=%%h"
set "BUILT=none"
if exist .next\BUILD_ID if exist .next\built-from.txt set /p BUILT=<.next\built-from.txt
if "%CODE%"=="unknown" if exist .next\BUILD_ID set "BUILT=unknown"

if not "%BUILT%"=="%CODE%" (
  echo Dashboard tayyar ho raha hai, 1-3 minute lagenge. Yeh sirf naye code ke baad hota hai...
  if exist .next rmdir /s /q .next
  call npm run build || (echo Dashboard build fail ho gaya. Upar error dekhein. & pause & exit /b 1)
  >.next\built-from.txt echo %CODE%
)

echo.
echo Dashboard chal raha hai: http://localhost:3000
call npm run start
echo.
echo Dashboard band ho gaya. Upar error dekhein.
pause
