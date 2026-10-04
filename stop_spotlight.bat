@echo off
title Stop PromptCompiler Spotlight
echo ========================================================
echo   Stopping PromptCompiler Spotlight Background Tasks
echo ========================================================

powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*desktop_app*' -or $_.CommandLine -like '*prompt_optimizer.web.app*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

echo.
echo [DONE] PromptCompiler background processes stopped.
pause
