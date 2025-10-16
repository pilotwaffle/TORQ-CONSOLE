@echo off
REM TORQ Console Launcher with GPU Acceleration
REM Sets up CUDA environment and launches the web interface

echo ========================================
echo TORQ Console - Starting...
echo ========================================
echo.

REM Add CUDA runtime and llama-cpp-python DLLs to PATH
set PATH=E:\Python\Python311\Lib\site-packages\nvidia\cuda_runtime\bin;E:\Python\Python311\Lib\site-packages\nvidia\cublas\bin;E:\Python\Python311\Lib\site-packages\llama_cpp\lib;%PATH%

REM Set environment variable to disable llama-cpp if missing
set LLAMA_CPP_OPTIONAL=1

REM Change to TORQ Console directory
cd /d "E:\TORQ-CONSOLE"

REM Launch TORQ Console web interface
echo Starting TORQ Console web server...
echo Opening browser at http://localhost:5000
echo.
echo Press Ctrl+C to stop the server.
echo ========================================
echo.

start http://localhost:5000

"E:\Python\Python311\python.exe" -m torq_console.ui.web
