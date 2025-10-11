@echo off
REM TORQ-CONSOLE UTF-8 Launcher
REM Fixes Unicode encoding issues on Windows

REM Set console code page to UTF-8
chcp 65001 >nul

REM Set Python to use UTF-8 encoding
set PYTHONIOENCODING=utf-8

REM Clear screen for clean startup
cls

echo Starting TORQ-CONSOLE with Prince Flowers agent...
echo.

REM Start TORQ-CONSOLE Web UI with Prince Flowers
python -m torq_console.ui.main

REM If the above fails, try direct launcher
if errorlevel 1 (
    echo.
    echo Trying direct launcher...
    python torq_console\ui\main.py
)
