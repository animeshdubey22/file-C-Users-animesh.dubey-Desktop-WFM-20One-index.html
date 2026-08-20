@echo off
title WFM-One Enterprise Server
cd /d "%~dp0"
echo ============================================================
echo   WFM-One Enterprise Workforce Management Server
echo ============================================================
echo Starting backend server on http://127.0.0.1:8000 ...
start "" "http://127.0.0.1:8000"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause

