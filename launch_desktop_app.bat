@echo off
title Personal Finance Agent (Desktop App)
echo ============================================================
echo   Starting Personal Finance Agent in Desktop App Window...
echo ============================================================
echo.

cd /d "%~dp0"

:: Verify virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in venv\
    pause
    exit /b 1
)

:: Start Backend if not already active
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Starting Backend Server...
    start "Finance Backend" /min cmd /c "venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend"
    timeout /t 2 /nobreak >nul
)

:: Start Frontend if not already active
netstat -ano | findstr ":8501" | findstr "LISTENING" >nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Starting Frontend Server...
    start "Finance Frontend" /min cmd /c "venv\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8501 --server.headless true"
    timeout /t 3 /nobreak >nul
)

:: Open in Standalone App Window Mode (using Edge or Chrome)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:8501
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:8501
) else (
    start "" "http://localhost:8501"
)
