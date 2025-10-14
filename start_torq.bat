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

REM Cross-platform delay using ping (works in cmd and Git Bash)
start /B cmd /c "ping 127.0.0.1 -n 4 > nul && start http://localhost:8899"

REM Start TORQ Console
"E:\Python\Python311\python.exe" "E:\TORQ-CONSOLE\torq_console\ui\main.py"
