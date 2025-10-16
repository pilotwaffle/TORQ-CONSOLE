@echo off
echo ========================================
echo Fixing TORQ Console Icon
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0fix_shortcut_icon.ps1"

echo.
echo Press any key to close...
pause >nul
