@echo off
title CyberSecAgent - Frontend
cd /d "%~dp0frontend-next"
set PATH=%PATH%;C:\Program Files\nodejs
echo Starting Frontend on http://localhost:3000
echo Press Ctrl+C to stop
npm run dev
pause
