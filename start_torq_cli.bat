@echo off
REM ========================================================================
REM TORQ Console CLI Startup Script - FIXED
REM ========================================================================
REM This script fixes the ModuleNotFoundError by using the correct
REM Python module invocation method.
REM
REM ISSUE: python -m torq_console.cli.main (WRONG - cli is a file, not package)
REM FIX: python -m torq_console.cli (CORRECT - cli.py has __main__ guard)
REM ========================================================================

cd /d "E:\TORQ-CONSOLE"

echo ================================================================================
echo TORQ CONSOLE v0.70.0 - Command Line Interface
echo ================================================================================
echo.
echo [OK] Environment: E:\TORQ-CONSOLE
echo [OK] Python: E:\Python\Python311\python.exe
echo [OK] Module: torq_console.cli (FIXED)
echo.
echo Starting TORQ Console in interactive mode...
echo Press Ctrl+C to exit
echo.
echo ================================================================================
echo.

REM Launch TORQ Console CLI using CORRECT module path
"E:\Python\Python311\python.exe" -m torq_console.cli -i

pause
