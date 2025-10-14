# Fix ALL TORQ Console shortcuts on desktop
# Finds all TORQ-related shortcuts and updates their icons

$desktopPath = [Environment]::GetFolderPath("Desktop")
$iconPath = "E:\TORQ-CONSOLE\torq_console_icon.ico"
$targetPath = "E:\TORQ-CONSOLE\torq_console\ui\web.py"
$pythonExe = "E:\Python\Python311\python.exe"

Write-Host "========================================"
Write-Host "Fixing ALL TORQ Console Shortcuts"
Write-Host "========================================"
Write-Host ""

# Find all .lnk files with "TORQ" in the name
$shortcuts = Get-ChildItem -Path $desktopPath -Filter "*.lnk" | Where-Object {
    $_.Name -like "*TORQ*" -or $_.Name -like "*torq*"
}

if ($shortcuts.Count -eq 0) {
    Write-Host "[WARNING] No TORQ shortcuts found on desktop"
    Write-Host ""
    Write-Host "Creating new shortcut..."

    # Create a new shortcut
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcutPath = Join-Path $desktopPath "TORQ Console (Prince Flowers).lnk"
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)

    $shortcut.TargetPath = $pythonExe
    $shortcut.Arguments = "`"$targetPath`""
    $shortcut.WorkingDirectory = "E:\TORQ-CONSOLE"
    $shortcut.IconLocation = $iconPath
    $shortcut.Description = "TORQ Console with Prince Flowers Enhanced Agent"
    $shortcut.WindowStyle = 1

    $shortcut.Save()
    Write-Host "[OK] Created: $shortcutPath"

} else {
    Write-Host "Found $($shortcuts.Count) TORQ shortcut(s):"
    Write-Host ""

    foreach ($file in $shortcuts) {
        Write-Host "  - $($file.Name)"

        # Update the shortcut
        $WScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $WScriptShell.CreateShortcut($file.FullName)

        # Update icon and properties
        $shortcut.IconLocation = $iconPath
        $shortcut.TargetPath = $pythonExe
        $shortcut.Arguments = "`"$targetPath`""
        $shortcut.WorkingDirectory = "E:\TORQ-CONSOLE"
        $shortcut.Description = "TORQ Console with Prince Flowers Enhanced Agent"

        $shortcut.Save()
        Write-Host "    [OK] Updated icon: $iconPath"
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "Refreshing icon cache and desktop..."
Write-Host "========================================"

# Clear icon cache
ie4uinit.exe -show

# Additional icon cache refresh
$iconCachePath = "$env:LOCALAPPDATA\IconCache.db"
if (Test-Path $iconCachePath) {
    Write-Host "Clearing icon cache database..."
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Remove-Item $iconCachePath -Force -ErrorAction SilentlyContinue
    Start-Process explorer
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========================================"
Write-Host "[SUCCESS] All TORQ shortcuts updated!"
Write-Host "========================================"
Write-Host ""
Write-Host "The new icon with the red T should now be visible."
Write-Host "If not, try:"
Write-Host "  1. Press F5 to refresh desktop"
Write-Host "  2. Right-click desktop > Refresh"
Write-Host "  3. Log out and log back in"
Write-Host ""
