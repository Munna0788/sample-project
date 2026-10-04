@echo off
title Install PromptCompiler to Windows Startup
echo ========================================================
echo   Adding PromptCompiler Spotlight to Windows Startup
echo ========================================================

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_TARGET=%~dp0start_silent.vbs
set SHORTCUT=%STARTUP_DIR%\PromptCompilerSpotlight.lnk

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_TARGET%\"'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 7; $s.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo [SUCCESS] PromptCompiler has been added to Windows Startup!
    echo Every time your laptop turns on, the service will start in the background.
    echo Pressing [Win + O] will automatically summon the box anytime.
) else (
    echo [ERROR] Could not create startup shortcut.
)
echo.
pause
