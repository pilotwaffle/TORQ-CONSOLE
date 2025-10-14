# Create TORQ Console + Prince Flowers Desktop Shortcut
# PowerShell script to create a desktop shortcut for TORQ Console web UI

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Creating TORQ CONSOLE + Prince Flowers Desktop Shortcut" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Get desktop path
$desktopPath = [Environment]::GetFolderPath('Desktop')
Write-Host "Desktop path: $desktopPath" -ForegroundColor Yellow
Write-Host ""

# Create shortcut
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $shortcutPath = Join-Path $desktopPath "TORQ Console + Prince Flowers.lnk"
    $shortcut = $WshShell.CreateShortcut($shortcutPath)

    # Set shortcut properties
    $shortcut.TargetPath = "E:\TORQ-CONSOLE\start_torq.bat"
    $shortcut.WorkingDirectory = "E:\TORQ-CONSOLE"
    $shortcut.Description = "TORQ Console Web UI with Prince Flowers Agent - Enhanced Learning Persistence"
    $shortcut.IconLocation = "E:\TORQ-CONSOLE\torq_console_icon.ico"
    $shortcut.WindowStyle = 1  # Normal window

    # Save the shortcut
    $shortcut.Save()

    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] Desktop shortcut created!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Shortcut Name:  TORQ Console + Prince Flowers.lnk" -ForegroundColor White
    Write-Host "Location:       $desktopPath" -ForegroundColor White
    Write-Host "Target:         E:\TORQ-CONSOLE\start_torq.bat" -ForegroundColor White
    Write-Host "Web UI:         http://127.0.0.1:8899" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Features:" -ForegroundColor Yellow
    Write-Host "  - Prince Flowers agent with learning persistence" -ForegroundColor White
    Write-Host "  - Enhanced RL system with continuous learning" -ForegroundColor White
    Write-Host "  - Auto-save every 10 queries" -ForegroundColor White
    Write-Host "  - Adaptive token allocation (1500-4000 tokens)" -ForegroundColor White
    Write-Host "  - Deep failure analysis" -ForegroundColor White
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "USAGE:" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "1. Double-click 'TORQ Console + Prince Flowers' on desktop" -ForegroundColor White
    Write-Host "2. Wait for server to start (console window will appear)" -ForegroundColor White
    Write-Host "3. Open browser to http://127.0.0.1:8899" -ForegroundColor White
    Write-Host "4. Start chatting with Prince Flowers!" -ForegroundColor White
    Write-Host ""
    Write-Host "Look for [PERSISTENCE] tags in console to see auto-saves." -ForegroundColor Yellow
    Write-Host ""

} catch {
    Write-Host "[ERROR] Failed to create shortcut: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Press any key to close..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
