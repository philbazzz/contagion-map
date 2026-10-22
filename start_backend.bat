@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0backend" || (echo [CONTAGION] Cannot enter backend folder. & pause & exit /b 1)

rem ---------------------------------------------------------------------------
rem Resolve a Python 3.10+ executable (needs working sqlite3 — skip QGIS/ETAP
rem bundles that break outside their host apps). Never call bare uvicorn.exe.
rem ---------------------------------------------------------------------------
set "PY_EXE="

rem Prefer official python.org installs first
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" call :try_py "%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PY_EXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" call :try_py "%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY_EXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" call :try_py "%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PY_EXE if exist "%LocalAppData%\Programs\Python\Python310\python.exe" call :try_py "%LocalAppData%\Programs\Python\Python310\python.exe"
if not defined PY_EXE if exist "%ProgramFiles%\Python312\python.exe" call :try_py "%ProgramFiles%\Python312\python.exe"
if not defined PY_EXE if exist "%ProgramFiles%\Python311\python.exe" call :try_py "%ProgramFiles%\Python311\python.exe"

if not defined PY_EXE (
  where py >nul 2>&1
  if not errorlevel 1 (
    for %%V in (3.13 3.12 3.11 3.10) do (
      if not defined PY_EXE (
        for /f "delims=" %%I in ('py -%%V -c "import sys; print(sys.executable)" 2^>nul') do call :try_py "%%I"
      )
    )
  )
)

if not defined PY_EXE (
  where python >nul 2>&1
  if not errorlevel 1 (
    for /f "delims=" %%P in ('where python 2^>nul') do (
      if not defined PY_EXE call :try_py "%%P"
    )
  )
)

if not defined PY_EXE (
  echo [CONTAGION] Python 3.10+ with working sqlite3 not found.
  echo Install from https://www.python.org/downloads/ ^(3.10+^)
  echo During setup, check "Add python.exe to PATH".
  echo Do not use ETAP Python 3.8 or QGIS embedded Python for this project.
  pause
  exit /b 1
)

echo [CONTAGION] Using Python:
"%PY_EXE%" -c "import sys; print(' ', sys.version.split()[0], '-', sys.executable)"
if errorlevel 1 (
  echo [CONTAGION] Selected Python failed to start: %PY_EXE%
  pause
  exit /b 1
)

rem ---------------------------------------------------------------------------
rem Virtualenv: recreate when missing, Python ^< 3.10, or deps incomplete
rem ---------------------------------------------------------------------------
set "NEED_VENV=0"
if not exist ".venv\Scripts\python.exe" set "NEED_VENV=1"

if "!NEED_VENV!"=="0" (
  .venv\Scripts\python.exe -c "import sys, sqlite3; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if errorlevel 1 (
    echo [CONTAGION] Existing .venv is outdated or broken ^(need Python 3.10+ + sqlite3^) — recreating...
    set "NEED_VENV=1"
  )
)

if "!NEED_VENV!"=="1" (
  if exist .venv (
    echo [CONTAGION] Removing broken/outdated .venv...
    rmdir /s /q .venv 2>nul
    if exist .venv (
      echo [CONTAGION] Could not remove .venv. Close programs using it and retry.
      pause
      exit /b 1
    )
  )
  echo [CONTAGION] Creating virtual environment...
  "%PY_EXE%" -m venv .venv
  if errorlevel 1 (
    echo [CONTAGION] Failed to create .venv with: %PY_EXE%
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo [CONTAGION] .venv\Scripts\python.exe missing after setup.
  pause
  exit /b 1
)

echo [CONTAGION] Ensuring pip and dependencies...
.venv\Scripts\python.exe -m ensurepip --upgrade >nul 2>&1
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
  echo [CONTAGION] pip upgrade failed.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo [CONTAGION] Dependency install failed. See errors above.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -c "import uvicorn, fastapi; print('[CONTAGION] OK — uvicorn', uvicorn.__version__, '| fastapi', fastapi.__version__)"
if errorlevel 1 (
  echo [CONTAGION] uvicorn/fastapi still not importable after install.
  pause
  exit /b 1
)

rem ---------------------------------------------------------------------------
rem Optional .env — missing keys do NOT block the API from starting
rem ---------------------------------------------------------------------------
if not exist .env (
  if exist .env.example (
    copy /y .env.example .env >nul
    echo [CONTAGION] Created backend\.env from .env.example ^(empty optional keys^).
  ) else (
    echo [CONTAGION] No backend\.env — market APIs will report "API key not set".
  )
  echo [CONTAGION] Optional API keys ^(see docs\MARKET_DATA.md^):
  echo   FRED_API_KEY, VASTAI_API_KEY, FINNHUB_API_KEY,
  echo   DATA_GO_KR_SERVICE_KEY, KOREAEXIM_API_KEY
) else (
  echo [CONTAGION] Using existing backend\.env
)

echo [CONTAGION] API starting at http://127.0.0.1:8000  ^(docs: /docs^)
echo [CONTAGION] Market data collects only while this window stays open.
echo [CONTAGION] Entry point: app.main:app via  python -m uvicorn
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
set "ERR=!errorlevel!"
if not "!ERR!"=="0" (
  echo.
  echo [CONTAGION] Backend exited with code !ERR!.
  echo Check messages above ^(imports, port 8000 in use, etc.^).
)
echo.
pause
endlocal & exit /b %ERR%

rem ---- helpers ----
:try_py
if defined PY_EXE goto :eof
"%~1" -c "import sys, sqlite3; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 set "PY_EXE=%~1"
goto :eof
