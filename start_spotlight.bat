@echo off
title PromptCompiler Spotlight Launcher
echo ========================================================
echo    Starting PromptCompiler Spotlight Box [Win + O]
echo ========================================================

set PYTHON_CMD=python
if exist "C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD="C:\Users\VICTUS\AppData\Local\Programs\Python\Python313\python.exe"
)

REM 1. Start FastAPI Backend in Background if not active
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if %errorlevel% neq 0 (
    echo [1/2] Launching Background API Server...
    start /b %PYTHON_CMD% -m uvicorn prompt_optimizer.web.app:app --host 0.0.0.0 --port 8000
    ping 127.0.0.1 -n 3 >nul
) else (
    echo [1/2] Background API Server is active on port 8000.
)

REM 2. Launch Desktop Spotlight Floating Window
echo [2/2] Launching Desktop Spotlight Box...
echo Global hotkeys active: [Win + O] or [Alt + O] anytime!
echo Press Esc to hide the box.
%PYTHON_CMD% -m prompt_optimizer.quick_box.desktop_app

pause
