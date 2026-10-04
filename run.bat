@echo off
title Prompt Compiler - Setup & Launcher
cls
echo ========================================================
echo        ⚡ PROMPT COMPILER - INSTANT LOCAL SETUP
echo ========================================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM 2. Install / verify dependencies
echo [1/3] Checking dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [WARN] Pip install had warnings, continuing...
)

REM 3. Start Background FastAPI Server if not running
echo [2/3] Checking Background Engine...
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if %errorlevel% neq 0 (
    echo Launching API server on http://localhost:8000...
    start /b python -m uvicorn prompt_optimizer.web.app:app --host 0.0.0.0 --port 8000
    ping 127.0.0.1 -n 3 >nul
) else (
    echo Background API server is already active on port 8000.
)

REM 4. Launch Desktop Spotlight HUD
echo [3/3] Launching Floating Spotlight Box [Win + O]...
echo.
echo ========================================================
echo  ✓ EVERYTHING IS RUNNING LOCALLY!
echo.
echo  • Global Hotkey: Press [Win + O] anytime to pop up!
echo  • Web Dashboard: http://localhost:8000
echo  • Spotlight Web: http://localhost:8000/spotlight.html
echo  • Press Esc anytime to hide the floating box.
echo ========================================================
echo.
python -m prompt_optimizer.quick_box.desktop_app
