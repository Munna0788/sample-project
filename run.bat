@echo off
title Prompt Compiler Launcher
cls
REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Run the universal launcher
python run.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Launcher exited with error code %errorlevel%
    pause
)
