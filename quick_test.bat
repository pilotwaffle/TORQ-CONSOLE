@echo off
echo.
echo ========================================
echo 🚀 TORQ CONSOLE Quick Test Script
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Error: Run this script from the TORQ-CONSOLE directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo 📁 Current directory: %CD%
echo.

REM Step 1: Check Python
echo 1️⃣ Checking Python installation...
python --version >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Python found:
    python --version
) else (
    py --version >nul 2>&1
    if %errorlevel%==0 (
        echo ✅ Python found:
        py --version
        set PYTHON_CMD=py
    ) else (
        echo ❌ Python not found! Please install Python 3.10+ from python.org
        pause
        exit /b 1
    )
)

if not defined PYTHON_CMD set PYTHON_CMD=python
echo.

REM Step 2: Install dependencies
echo 2️⃣ Installing TORQ CONSOLE...
%PYTHON_CMD% -m pip install -e . >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Installation successful
) else (
    echo ❌ Installation failed. Trying with user install...
    %PYTHON_CMD% -m pip install --user -e .
)
echo.

REM Step 3: Initialize configuration
echo 3️⃣ Initializing configuration...
%PYTHON_CMD% -m torq_console.cli config-init >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Configuration initialized
) else (
    echo ⚠️ Configuration may already exist
)
echo.

REM Step 4: Run tests
echo 4️⃣ Running integration tests...
%PYTHON_CMD% test_integration.py
echo.

REM Step 5: Show available commands
echo 5️⃣ Available commands:
echo.
echo 🔧 Basic Commands:
echo   %PYTHON_CMD% -m torq_console.cli --help
echo   %PYTHON_CMD% -m torq_console.cli --interactive
echo   %PYTHON_CMD% -m torq_console.cli --web
echo.
echo 🎯 MCP Commands:
echo   %PYTHON_CMD% -m torq_console.cli mcp --endpoint http://localhost:3100
echo   %PYTHON_CMD% -m torq_console.cli edit "your message" --ideate
echo.
echo 🎨 Visual Commands:
echo   %PYTHON_CMD% -m torq_console.cli diff --tool delta
echo   %PYTHON_CMD% demo.py
echo.

REM Step 6: Quick demo option
echo 6️⃣ Quick Demo Options:
echo.
set /p choice="Run demo now? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo 🎬 Running TORQ CONSOLE demo...
    %PYTHON_CMD% demo.py
)

echo.
echo 🎉 TORQ CONSOLE is ready!
echo.
echo 💡 Next steps:
echo   1. Start your MCP servers: E:\start_hybrid_mcp.bat
echo   2. Try: %PYTHON_CMD% -m torq_console.cli --interactive
echo   3. Or:  %PYTHON_CMD% -m torq_console.cli --web
echo.
pause