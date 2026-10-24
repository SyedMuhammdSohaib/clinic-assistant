@echo off
rem Starts PostgreSQL (if it is not already running), the backend and the dashboard,
rem then opens both pages. Run from the repository root.
rem Set PGBIN and PGDATA below (or as environment variables) to your PostgreSQL install.
rem If PostgreSQL runs as a Windows service, it is already up and this step is skipped.

if not defined PGBIN set "PGBIN=C:\Program Files\PostgreSQL\17\bin"
if not defined PGDATA set "PGDATA=C:\Program Files\PostgreSQL\17\data"

if not exist "%~dp0run-backend.bat" (
  echo run-backend.bat nahi mila. run-backend.example.bat ko copy karke apni keys bharein.
  pause
  exit /b 1
)

rem PGBIN not found: assume PostgreSQL runs as a Windows service and go on.
if not exist "%PGBIN%\pg_isready.exe" (
  echo PostgreSQL folder nahi mila, maan rahe hain ke database service ki tarah chal raha hai.
  goto dbready
)
"%PGBIN%\pg_isready" -q -h localhost -p 5432
if not errorlevel 1 goto dbready

if not exist "%PGDATA%\PG_VERSION" (
  echo Database folder nahi mila: %PGDATA%
  echo start.bat mein PGBIN aur PGDATA theek karein.
  pause
  exit /b 1
)
echo Database start ho raha hai, 1-2 minute lag sakte hain...
rem Closing this window stops the database, so it starts minimized with a clear title.
start "Clinic DATABASE - is window ko band na karein" /min cmd /k ""%PGBIN%\pg_ctl" -D "%PGDATA%" -l "%PGDATA%\log\manual.log" start"

set /a tries=0
:waitdb
"%PGBIN%\pg_isready" -q -h localhost -p 5432
if not errorlevel 1 goto dbready
set /a tries+=1
if %tries% geq 120 (
  echo.
  echo Database 2 minute mein start nahi hua. "Clinic DATABASE" window mein error dekhein.
  pause
  exit /b 1
)
timeout /t 1 /nobreak >nul
goto waitdb

:dbready
echo Database chal raha hai.
start "Clinic backend" cmd /k "%~dp0run-backend.bat"
start "Clinic dashboard" cmd /k "%~dp0run-dashboard.bat"
echo Servers start ho rahe hain. Naye code ke baad dashboard banne mein 1-3 minute lagte hain...
rem Open the pages once the dashboard answers (curl comes with Windows 10 and 11), at most 5 minutes.
set /a waited=0
:waitweb
timeout /t 5 /nobreak >nul
set /a waited+=5
curl -s -o nul http://localhost:3000 && goto webready
if %waited% lss 300 goto waitweb
echo Dashboard 5 minute mein tayyar nahi hua. "Clinic dashboard" window mein error dekhein.
:webready
start "" "http://127.0.0.1:8000/app/"
start "" "http://localhost:3000"
