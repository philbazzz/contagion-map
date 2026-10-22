@echo off
setlocal
cd /d "%~dp0frontend"
echo.
echo  CONTAGION — one-click static preview (no Python API server)
echo  ===========================================================
echo.
where node >nul 2>&1 || (echo Node.js not found. Install from https://nodejs.org & pause & exit /b 1)
where python >nul 2>&1 || (echo Python not found. Needed once to export network.json & pause & exit /b 1)

if not exist node_modules (
  echo Installing npm packages...
  call npm ci || call npm install
)

echo Preparing static data + building...
set VITE_API_MODE=static
set VITE_BASE=./
call npm run build
if errorlevel 1 (echo Build failed. & pause & exit /b 1)

echo.
echo Opening http://127.0.0.1:4173  (Ctrl+C to stop)
echo.
call npx vite preview --host 127.0.0.1 --port 4173
endlocal
