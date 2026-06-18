@echo off
title CyberSecAgent - Starting...
cd /d "%~dp0"

echo ========================================
echo   CyberSecAgent - Full Stack Startup
echo ========================================
echo.

:: Start Backend in new window
echo Starting Backend...
start "Backend - FastAPI" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"

:: Wait a moment for backend to start
timeout /t 3 /nobreak > nul

:: Start Frontend in new window
echo Starting Frontend...
start "Frontend - Next.js" cmd /k "cd /d %~dp0frontend-next && set PATH=%PATH%;C:\Program Files\nodejs && npm run dev"

echo.
echo ========================================
echo   Both servers starting!
echo ========================================
echo.
echo   Backend:  http://localhost:8003
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8003/docs
echo.
echo   Close the terminal windows to stop.
echo ========================================
pause
