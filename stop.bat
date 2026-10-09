@echo off
title Stop Personal Finance Agent
echo Stopping Personal Finance Agent services...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Terminating backend process PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501" ^| findstr "LISTENING"') do (
    echo Terminating frontend process PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo Services stopped.
timeout /t 2 >nul
