@echo off
REM TORQ Chrome Bridge - Windows Launcher
REM This script launches the native messaging host for Chrome
REM
REM Modes:
REM   Normal (default): Native messaging + HTTP API (launched by Chrome extension)
REM   HTTP-only: Set NO_NATIVE_MESSAGING=1 for Railway/tunnel testing

REM Configuration
setlocal

REM Set API key (change this to a secure random string)
if not defined CHROME_BRIDGE_API_KEY (
    set CHROME_BRIDGE_API_KEY=torq-bridge-change-me
)

REM Set host and port
if not defined CHROME_BRIDGE_HOST (
    set CHROME_BRIDGE_HOST=127.0.0.1
)

if not defined CHROME_BRIDGE_PORT (
    set CHROME_BRIDGE_PORT=4545
)

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Add to Python path
set PYTHONPATH=%SCRIPT_DIR%..;%PYTHONPATH%

REM Check for HTTP-only mode
if "%NO_NATIVE_MESSAGING%"=="1" (
    echo Starting TORQ Chrome Bridge [HTTP-ONLY MODE]...
    echo This mode is for Railway/tunnel testing (no Chrome extension connection)
) else (
    echo Starting TORQ Chrome Bridge [NATIVE MESSAGING MODE]...
    echo Chrome extension will connect automatically when clicked
)

echo Host: %CHROME_BRIDGE_HOST%:%CHROME_BRIDGE_PORT%
echo.

REM Launch the host
python "%SCRIPT_DIR%host.py"

pause
