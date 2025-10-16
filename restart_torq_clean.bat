@echo off
echo Stopping all TORQ Console processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *TORQ*" 2>nul
timeout /t 2 /nobreak >nul

echo Clearing Python cache...
cd /d E:\Torq-Console
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo Starting TORQ Console with fixes...
python start_torq_with_fixes.py

pause
