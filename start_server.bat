@echo off
title WFM-One Backend Server
cd /d "%~dp0"
echo Starting WFM-One FastAPI Backend Server on http://localhost:8000/ ...
python main.py
pause
