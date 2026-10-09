@echo off
title Personal Finance Agent Launcher
echo ============================================================
echo   Personal Finance Agent: AI Budget & Spending Assistant
echo ============================================================
echo.

cd /d "%~dp0"

:: Verify virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in venv\
    echo Please make sure the venv is configured.
    pause
    exit /b 1
)

:: Check if backend is already running on port 8000
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Backend is already running on port 8000.
) else (
    echo [INFO] Starting Backend Server (FastAPI on port 8000)...
    start "Finance Backend" /min cmd /c "venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend"
    timeout /t 2 /nobreak >nul
)

:: Check if frontend is already running on port 8501
netstat -ano | findstr ":8501" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Frontend is already running on port 8501.
    start "" "http://localhost:8501"
) else (
    echo [INFO] Starting Frontend UI (Streamlit on port 8501)...
    start "Finance Frontend" cmd /c "venv\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8501"
)

echo.
echo ============================================================
echo   Application started successfully!
echo   Frontend: http://localhost:8501
echo   Backend API: http://localhost:8000/docs
echo ============================================================
timeout /t 5
