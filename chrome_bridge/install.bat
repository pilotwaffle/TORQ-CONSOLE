@echo off
REM TORQ Chrome Bridge - Windows Installation Script
REM This script registers the native messaging host with Chrome

setlocal enabledelayedexpansion

echo ==========================================
echo TORQ Chrome Bridge - Installation
echo ==========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo Script directory: %SCRIPT_DIR%
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.10+ and add it to PATH
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Install dependencies
echo [1/4] Installing Python dependencies...
pip install -q fastapi uvicorn pydantic
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Create manifest with correct paths
echo [2/4] Creating native host manifest...
set MANIFEST_FILE=%SCRIPT_DIR%\com.torq.chrome_bridge.json

(
echo {
echo   "name": "com.torq.chrome_bridge",
echo   "description": "TORQ Native Messaging Host for Prince Flowers Agent",
echo   "path": "%SCRIPT_DIR%\run_host.bat",
echo   "type": "stdio",
echo   "allowed_origins": ["chrome-extension://*"]
echo }
) > "%MANIFEST_FILE%"

echo [OK] Manifest created: %MANIFEST_FILE%
echo.

REM Register with Chrome
echo [3/4] Registering with Chrome...

REM Get Chrome user data directory
set CHROME_KEY=HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts

REM Create registry key
reg add "%CHROME_KEY%\com.torq.chrome_bridge" /ve /t REG_SZ /d "%MANIFEST_FILE%" /f >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to register with Chrome via registry
    echo You may need to run this script as Administrator
) else (
    echo [OK] Registered with Chrome
)
echo.

REM Check for Edge too
reg add "HKEY_CURRENT_USER\Software\Microsoft Edge\NativeMessagingHosts\com.torq.chrome_bridge" /ve /t REG_SZ /d "%MANIFEST_FILE%" /f >nul 2>&1
if not errorlevel 1 (
    echo [OK] Also registered with Microsoft Edge
)
echo.

REM Create desktop shortcut
echo [4/4] Creating desktop shortcut...
set SHORTCUT=%USERPROFILE%\Desktop\TORQ Chrome Bridge.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%SCRIPT_DIR%\run_host.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"
if exist "%SHORTCUT%" (
    echo [OK] Shortcut created: %SHORTCUT%
) else (
    echo [WARNING] Failed to create shortcut
)
echo.

REM Set up API key
if not exist "%SCRIPT_DIR%\.env" (
    echo Creating .env file with API key...
    echo CHROME_BRIDGE_API_KEY=tork-bridge-%RANDOM%-%RANDOM% > "%SCRIPT_DIR%\.env"
    echo CHROME_BRIDGE_HOST=127.0.0.1 >> "%SCRIPT_DIR%\.env"
    echo CHROME_BRIDGE_PORT=4545 >> "%SCRIPT_DIR%\.env"
    echo [OK] Created .env with random API key
    echo.
)

echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Load the Chrome extension:
echo    - Open chrome://extensions/
echo    - Enable Developer mode
echo    - Click "Load unpacked"
echo    - Select: %SCRIPT_DIR%\..\chrome_extension
echo.
echo 2. Copy the extension ID from chrome://extensions/
echo    - Replace YOUR_EXTENSION_ID in the manifest if needed
echo.
echo 3. Start the bridge:
echo    - Double-click the desktop shortcut, OR
echo    - Run: %SCRIPT_DIR%\run_host.bat
echo.
echo 4. Test the connection:
echo    - Click the extension icon
echo    - Status should show "Connected"
echo.

pause
