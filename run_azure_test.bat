@echo off
REM Test script for Prince Flowers + Llama + Azure Research
REM
echo ====================================================================
echo PRINCE FLOWERS + LLAMA + AZURE RESEARCH TEST
echo ====================================================================
echo.

cd /d E:\TORQ-CONSOLE

REM Try Python 3.13
echo Checking Python 3.13...
if exist "C:\Users\asdasd\AppData\Local\Programs\Python\Python313\python.exe" (
    echo Found Python 3.13
    "C:\Users\asdasd\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_prince_llama_azure_research.py -v -s
    echo.
    echo Test completed.
    pause
    exit /b %errorlevel%
)

REM Try Python 3.12
echo Checking Python 3.12...
if exist "C:\Users\asdasd\AppData\Local\Programs\Python\Python312\python.exe" (
    echo Found Python 3.12
    "C:\Users\asdasd\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests\test_prince_llama_azure_research.py -v -s
    echo.
    echo Test completed.
    pause
    exit /b %errorlevel%
)

REM Try system python
echo Checking system Python...
python -m pytest tests\test_prince_llama_azure_research.py -v -s
if errorlevel 1 (
    echo.
    echo ERROR: Python not found. Please install Python 3.12+ or add to PATH
    pause
    exit /b 1
)

pause
