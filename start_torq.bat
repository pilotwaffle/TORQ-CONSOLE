@echo off
cd /d "E:\TORQ-CONSOLE"

REM Add all necessary DLLs to PATH for GPU acceleration
set PATH=E:\Python\Python311\Lib\site-packages\nvidia\cuda_runtime\bin;E:\Python\Python311\Lib\site-packages\nvidia\cublas\bin;E:\Python\Python311\Lib\site-packages\llama_cpp\lib;%PATH%

REM Display startup info
echo ================================================================================
echo TORQ CONSOLE v0.70.0 - GPU-Accelerated AI Development Environment
echo ================================================================================
echo.
echo [OK] CUDA DLLs added to PATH
echo [OK] GPU acceleration enabled (28 layers)
echo [OK] Starting TORQ Console...
echo.
echo Server will be available at: http://localhost:8899
echo Opening browser in 3 seconds...
echo.

REM Start TORQ Console in background
start "TORQ Console Server" /B "E:\Python\Python311\python.exe" "E:\TORQ-CONSOLE\torq_console\ui\main.py"

REM Wait for server to start (5 seconds)
timeout /t 5 /nobreak > nul

REM Open browser to TORQ Console
start http://localhost:8899

REM Keep window open to show server logs
echo.
echo ================================================================================
echo TORQ Console is running! Browser should open automatically.
echo If browser didn't open, navigate to: http://localhost:8899
echo Press Ctrl+C to stop the server.
echo ================================================================================
echo.

REM Wait indefinitely to keep the server running
pause > nul
