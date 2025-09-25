@echo off
echo Creating TORQ CONSOLE Desktop Shortcut...

REM Get the desktop path
for /f "tokens=3*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop') do set DESKTOP=%%j

REM Create the shortcut using PowerShell
powershell -Command ^
"$WshShell = New-Object -comObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\TORQ CONSOLE.lnk'); ^
$Shortcut.TargetPath = 'E:\Python\Python311\python.exe'; ^
$Shortcut.Arguments = '-m torq_console.cli --interactive'; ^
$Shortcut.WorkingDirectory = 'E:\TORQ-CONSOLE'; ^
$Shortcut.Description = 'TORQ CONSOLE - Enhanced AI Pair Programming'; ^
$Shortcut.IconLocation = 'E:\TORQ-CONSOLE\torq_icon.ico'; ^
$Shortcut.Save()"

echo.
echo ✓ Desktop shortcut created: TORQ CONSOLE.lnk
echo ✓ Target: E:\Python\Python311\python.exe -m torq_console.cli --interactive
echo ✓ Working Directory: E:\TORQ-CONSOLE
echo.
echo Double-click the desktop icon to start TORQ CONSOLE!
echo.
pause