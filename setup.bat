@echo off
rem One-time setup on a new computer. Safe to run again.
rem Needs: Python, Node.js, PostgreSQL running, and run-backend.bat filled in.
title Clinic setup
cd /d "%~dp0"

if not exist run-backend.bat (
  echo run-backend.bat nahi mili. run-backend.example.bat ko Notepad mein kholein,
  echo values bharein aur "Save As" se run-backend.bat naam se save karein.
  pause
  exit /b 1
)
where python >nul 2>nul || (echo Python install nahi hai. python.org se install karein, "Add to PATH" tick karein. & pause & exit /b 1)
where npm >nul 2>nul || (echo Node.js install nahi hai. nodejs.org se LTS install karein. & pause & exit /b 1)

echo.
echo [1/4] Python ka setup...
if not exist .venv\Scripts\python.exe python -m venv .venv || (echo .venv nahi ban saka & pause & exit /b 1)
.venv\Scripts\python -m pip install -q -r backend\requirements.txt || (echo Python packages install nahi hue & pause & exit /b 1)

echo.
echo [2/4] Apna phone number likhein taake aap parent app mein login kar sakein.
set "PHONE="
set /p "PHONE=Number (jaise 03001234567), ya sirf Enter dabayein: "

echo.
echo [3/4] Database aur settings...
.venv\Scripts\python backend\scripts\setup_local.py run-backend.bat --phone "%PHONE%" || (pause & exit /b 1)

echo.
echo [4/4] Dashboard ka setup (2-3 minute)...
pushd dashboard
call npm install --no-fund --no-audit || (popd & echo npm install fail ho gaya & pause & exit /b 1)
popd

echo.
echo ===============================================
echo  Setup mukammal! Ab start.bat chalayein.
echo ===============================================
pause
