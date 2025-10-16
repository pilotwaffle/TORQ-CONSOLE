@echo off
echo Refreshing Windows Icon Cache...
echo.

REM Clear icon cache
ie4uinit.exe -show

REM Restart Windows Explorer
echo Restarting Windows Explorer...
taskkill /F /IM explorer.exe
start explorer.exe

echo.
echo [SUCCESS] Icon cache refreshed!
echo The desktop shortcut icon should now display correctly.
echo.
pause
