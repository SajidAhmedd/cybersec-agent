@echo off
title CyberSecAgent - Backend
cd /d "%~dp0"
call venv\Scripts\activate
echo Starting Backend on http://localhost:8003
echo Press Ctrl+C to stop
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
pause
