@echo off
echo ========================================
echo TORQ Console Icon Refresh Tool
echo ========================================
echo.
echo This will update all TORQ Console shortcuts
echo with the red T icon design.
echo.
echo Press any key to continue...
pause >nul

powershell -ExecutionPolicy Bypass -File "%~dp0fix_all_torq_shortcuts.ps1"

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo The icon should now be visible on your desktop.
echo Press F5 to refresh if needed.
echo.
echo Press any key to close...
pause >nul
