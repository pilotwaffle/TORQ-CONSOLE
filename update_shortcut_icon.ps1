
# Update TORQ Console Desktop Shortcut Icon
# Quick script to update existing shortcut with new TORQ icon

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "TORQ Console + Prince Flowers.lnk"

Write-Host ""
Write-Host "Updating desktop shortcut with TORQ icon..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path $shortcutPath) {
    $WshShell = New-Object -ComObject WScript.Shell
    $shortcut = $WshShell.CreateShortcut($shortcutPath)
    $shortcut.IconLocation = "E:\TORQ-CONSOLE\torq_console_icon.ico"
    $shortcut.Save()

    Write-Host "[SUCCESS] Shortcut icon updated!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Icon: E:\TORQ-CONSOLE\torq_console_icon.ico" -ForegroundColor White
    Write-Host ""
    Write-Host "The TORQ Console logo is now displayed on your desktop shortcut." -ForegroundColor White
} else {
    Write-Host "[ERROR] Shortcut not found at: $shortcutPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run Create-DesktopShortcut.ps1 first to create the shortcut." -ForegroundColor Yellow
}

Write-Host ""
