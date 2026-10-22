@echo off
cd /d "%~dp0backend"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python -m pytest -q
pause
