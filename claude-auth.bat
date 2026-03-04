@echo off
REM Claude Code Authentication Switcher (Windows)
REM Easily toggle between API key and Claude Pro subscription

setlocal enabledelayedexpansion

set CONFIG_DIR=%USERPROFILE%\.claude
set SETTINGS_FILE=%CONFIG_DIR%\settings.json
set API_SETTINGS_BACKUP=%CONFIG_DIR%\settings.json.api_backup
set CREDENTIALS_BACKUP=%CONFIG_DIR%\.credentials.json.api_backup

if "%1"=="" goto status
if /i "%1"=="status" goto status
if /i "%1"=="sub" goto subscription
if /i "%1"=="pro" goto subscription
if /i "%1"=="claudeai" goto subscription
if /i "%1"=="api" goto api
if /i "%1"=="key" goto api
if /i "%1"=="help" goto help
goto status

:subscription
echo [Auth Switcher] Switching to Claude Pro Subscription...
echo.

REM Save current API config
if exist "%SETTINGS_FILE%" (
    findstr /C:"ANTHROPIC_AUTH_TOKEN" "%SETTINGS_FILE%" >nul 2>&1
    if not errorlevel 1 (
        copy "%SETTINGS_FILE%" "%API_SETTINGS_BACKUP%" >nul 2>&1
        echo [Auth Switcher] API configuration saved
    )
)

REM Update settings using Python
python -c "import json, os; f = os.path.expanduser('~/.claude/settings.json'); s = json.load(open(f)); s.get('env', {}).clear(); [s['env'].pop(k, None) for k in ['ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','ANTHROPIC_DEFAULT_OPUS_MODEL','ANTHROPIC_DEFAULT_SONNET_MODEL','ANTHROPIC_DEFAULT_GLM_MODEL','ANTHROPIC_AVAILABLE_MODELS','ANTHROPIC_DEFAULT_GLM_47_MODEL','CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'] if k in s.get('env', {})]; s['forceLoginMethod'] = 'claudeai'; s['model'] = 'claude-opus-4-6'; json.dump(s, open(f, 'w'), indent=2); print('Settings updated')"

REM Backup and clear credentials
if exist "%CONFIG_DIR%\.credentials.json" (
    move "%CONFIG_DIR%\.credentials.json" "%CREDENTIALS_BACKUP%" >nul 2>&1
)

echo.
echo [Auth Switcher] Switched to Claude Pro Subscription
echo.
echo [Auth Switcher] Please restart Claude Code and login with your Claude account
goto end

:api
echo [Auth Switcher] Switching to API Key...
echo.

if not exist "%API_SETTINGS_BACKUP%" (
    echo [Auth Switcher] No saved API configuration found
    echo.
    echo To set up API authentication:
    echo   1. Get your API key from https://console.anthropic.com/
    echo   2. Run: claude auth
    echo   3. Or manually add to settings.json
    goto end
)

REM Restore API configuration
copy "%API_SETTINGS_BACKUP%" "%SETTINGS_FILE%" >nul 2>&1
if exist "%CREDENTIALS_BACKUP%" (
    copy "%CREDENTIALS_BACKUP%" "%CONFIG_DIR%\.credentials.json" >nul 2>&1
)

REM Remove forceLoginMethod
python -c "import json, os; f = os.path.expanduser('~/.claude/settings.json'); s = json.load(open(f)); s.pop('forceLoginMethod', None); json.dump(s, open(f, 'w'), indent=2); print('Settings updated')"

echo.
echo [Auth Switcher] Switched to API Key
echo.
echo [Auth Switcher] Please restart Claude Code
goto end

:status
echo.
echo ==========================================
echo   Claude Code Authentication Status
echo ==========================================
echo.

if exist "%SETTINGS_FILE%" (
    findstr /C:"forceLoginMethod.*claudeai" "%SETTINGS_FILE%" >nul 2>&1
    if not errorlevel 1 (
        echo Current Mode: Claude Pro Subscription
    ) else (
        findstr /C:"ANTHROPIC_AUTH_TOKEN" "%SETTINGS_FILE%" >nul 2>&1
        if not errorlevel 1 (
            echo Current Mode: API Key
            for /f "tokens=2 delims=:" %%A in ('findstr "ANTHROPIC_BASE_URL" "%SETTINGS_FILE%"') do (
                set URL_LINE=%%A
                set URL_LINE=!URL_LINE:"=!
                set URL_LINE=!URL_LINE:,=!
                echo API Endpoint: !URL_LINE:~0,-1!
            )
        ) else (
            echo Current Mode: Default/Unknown
        )
    )
) else (
    echo Status: No settings file found
)

echo.
echo ==========================================
echo.
echo Usage: claude-auth [mode]
echo.
echo   sub, pro      - Switch to Claude Pro Subscription
echo   api, key      - Switch to API Key
echo   status        - Show current status (default)
echo.
goto end

:help
echo Claude Code Authentication Switcher
echo.
echo Usage: claude-auth [mode]
echo.
echo Modes:
echo   sub, pro, subscription  Switch to Claude Pro Subscription
echo   api, key               Switch to API Key
echo   status, --status       Show current authentication mode
echo.
echo Examples:
echo   claude-auth sub         Switch to subscription
echo   claude-auth api         Switch to API key
echo   claude-auth status      Show current mode
echo.

:end
endlocal
