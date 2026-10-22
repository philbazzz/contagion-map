@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0" || (echo [CONTAGION] Cannot enter project root. & pause & exit /b 1)

rem =============================================================================
rem CONTAGION — single-command local launch (backend :8000 + frontend :5173)
rem Ctrl+C or closing this window stops both services.
rem =============================================================================

echo.
echo  CONTAGION — starting backend + frontend
echo  ========================================
echo.

rem ---- Node ----
if exist "%ProgramFiles%\nodejs\npm.cmd" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "%LocalAppData%\Programs\nodejs\npm.cmd" set "PATH=%LocalAppData%\Programs\nodejs;%PATH%"
where npm >nul 2>&1
if errorlevel 1 (
  echo [CONTAGION] Node.js / npm not found. Install Node.js 18+ LTS from https://nodejs.org/
  pause
  exit /b 1
)

rem ---- Backend venv (reuse start_backend.bat resolution via nested call pattern) ----
if not exist "backend\.venv\Scripts\python.exe" (
  echo [CONTAGION] Backend venv missing — running start_backend setup once...
  echo [CONTAGION] After deps install, re-run start.bat if this window only started the API.
  call "%~dp0start_backend.bat"
  exit /b %errorlevel%
)

if not exist "frontend\node_modules\" (
  echo [CONTAGION] Installing frontend packages...
  pushd frontend
  call npm install
  if errorlevel 1 (popd & echo [CONTAGION] npm install failed. & pause & exit /b 1)
  popd
)

set "VITE_API_MODE=http"
set "VITE_BASE=./"
set "BACKEND_PID="
set "FRONTEND_PID="

echo [CONTAGION] Backend  http://127.0.0.1:8000  ^(uvicorn^)
echo [CONTAGION] Frontend http://127.0.0.1:5173  ^(Vite, proxy /api -^> :8000^)
echo [CONTAGION] Press Ctrl+C to stop both.
echo.

rem Start backend in a minimized window we can track
start "contagion-backend" /MIN cmd /c "cd /d \"%~dp0backend\" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
if errorlevel 1 (
  echo [CONTAGION] Failed to start backend.
  pause
  exit /b 1
)

rem Wait until /api/health answers (max ~45s)
set "READY=0"
for /L %%i in (1,1,45) do (
  powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/api/health -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 (
    set "READY=1"
    echo [CONTAGION] Backend ready.
    goto :front
  )
  timeout /t 1 /nobreak >nul
)
echo [CONTAGION] WARNING: Backend health check timed out — frontend will still start.
echo [CONTAGION] If API calls fail, check the contagion-backend window or port 8000.

:front
start "" http://127.0.0.1:5173
pushd frontend
call npm run dev -- --host 127.0.0.1 --port 5173
set "ERR=!errorlevel!"
popd

echo.
echo [CONTAGION] Frontend stopped ^(code !ERR!^). Stopping backend...
taskkill /FI "WINDOWTITLE eq contagion-backend*" /T /F >nul 2>&1
rem Also kill uvicorn on 8000 if title match failed
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
  taskkill /PID %%P /T /F >nul 2>&1
)

if not "!ERR!"=="0" (
  echo [CONTAGION] Frontend exited with code !ERR!.
  pause
)
endlocal & exit /b %ERR%
