@echo off
REM TORQ Chrome Bridge - HTTP-Only Mode Launcher
REM
REM Use this mode when:
REM - Testing the HTTP API without Chrome extension
REM - Running with a tunnel (Cloudflare, ngrok) for Railway access
REM - The extension is NOT needed for basic HTTP testing

setlocal

REM Enable HTTP-only mode
set NO_NATIVE_MESSAGING=1

REM Use a strong API key for production
if not defined CHROME_BRIDGE_API_KEY (
    set CHROME_BRIDGE_API_KEY=torq-bridge-change-me
)

REM Listen on all interfaces (required for tunnel)
set CHROME_BRIDGE_HOST=0.0.0.0

if not defined CHROME_BRIDGE_PORT (
    set CHROME_BRIDGE_PORT=4545
)

echo ==========================================
echo TORQ Chrome Bridge - HTTP-Only Mode
echo ==========================================
echo.
echo This mode runs the HTTP API server without
echo Chrome Native Messaging. Use this for:
echo   - Railway tunnel connections
echo   - API testing without extension
echo   - Headless browser operations
echo.
echo Server: http://%CHROME_BRIDGE_HOST%:%CHROME_BRIDGE_PORT%
echo.
echo To connect Railway:
echo   1. Start a tunnel (cloudflared, ngrok, etc.)
echo      cloudflared tunnel --url http://127.0.0.1:4545
echo   2. Copy the tunnel URL
echo   3. Set Railway env: CHROME_BRIDGE_URL=https://your-tunnel-url
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set PYTHONPATH=%SCRIPT_DIR%..;%PYTHONPATH%

python "%SCRIPT_DIR%host.py"
