@echo off
echo ============================================================
echo Creating TORQ CONSOLE + Prince Flowers Desktop Shortcut
echo ============================================================
echo.

REM Get the desktop path
for /f "tokens=3*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop') do set DESKTOP=%%j

echo Desktop path: %DESKTOP%
echo.

REM Create the shortcut using PowerShell
powershell -Command ^
"$WshShell = New-Object -comObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\TORQ Console + Prince Flowers.lnk'); ^
$Shortcut.TargetPath = 'E:\TORQ-CONSOLE\start_torq.bat'; ^
$Shortcut.WorkingDirectory = 'E:\TORQ-CONSOLE'; ^
$Shortcut.Description = 'TORQ Console Web UI with Prince Flowers Agent - Enhanced Learning Persistence'; ^
$Shortcut.IconLocation = 'E:\Python\Python311\python.exe,0'; ^
$Shortcut.WindowStyle = 1; ^
$Shortcut.Save()"

echo.
echo ============================================================
echo [SUCCESS] Desktop shortcut created!
echo ============================================================
echo.
echo Shortcut Name: TORQ Console + Prince Flowers.lnk
echo Location:      %DESKTOP%
echo Target:        E:\TORQ-CONSOLE\start_torq.bat
echo Description:   Launches TORQ Console web UI at http://127.0.0.1:8899
echo Features:      - Prince Flowers agent with learning persistence
echo                - Enhanced RL system with continuous learning
echo                - Auto-save every 10 queries
echo                - Adaptive token allocation
echo.
echo ============================================================
echo USAGE:
echo ============================================================
echo 1. Double-click the desktop icon to start TORQ Console
echo 2. Wait for "Starting TORQ-CONSOLE with Prince Flowers agent..."
echo 3. Open your browser to http://127.0.0.1:8899
echo 4. Start chatting with Prince Flowers!
echo.
echo The console window will show server logs and persistence messages.
echo Look for [PERSISTENCE] tags to see learning auto-saves.
echo.
pause
