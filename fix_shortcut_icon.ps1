# Fix TORQ Console Desktop Shortcut Icon
# Run this script as Administrator

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "TORQ Console (Prince Flowers).lnk"
$iconPath = "E:\TORQ-CONSOLE\torq_console_icon.ico"
$targetPath = "E:\TORQ-CONSOLE\torq_console\ui\web.py"
$pythonExe = "E:\Python\Python311\python.exe"

Write-Host "========================================"
Write-Host "Fixing TORQ Console Shortcut Icon"
Write-Host "========================================"
Write-Host ""

# Check if shortcut exists
if (Test-Path $shortcutPath) {
    Write-Host "[OK] Found shortcut at: $shortcutPath"

    # Create WScript Shell object
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)

    # Update shortcut properties
    $shortcut.TargetPath = $pythonExe
    $shortcut.Arguments = "`"$targetPath`""
    $shortcut.WorkingDirectory = "E:\TORQ-CONSOLE"
    $shortcut.IconLocation = $iconPath
    $shortcut.Description = "TORQ Console with Prince Flowers Enhanced Agent"
    $shortcut.WindowStyle = 1  # Normal window

    # Save the shortcut
    $shortcut.Save()

    Write-Host "[OK] Shortcut updated successfully!"
    Write-Host "[OK] Icon: $iconPath"
    Write-Host ""
    Write-Host "Please refresh your desktop (press F5) to see the new icon."

} else {
    Write-Host "[ERROR] Shortcut not found at: $shortcutPath"
    Write-Host ""
    Write-Host "Creating new shortcut..."

    # Create the shortcut
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)

    $shortcut.TargetPath = $pythonExe
    $shortcut.Arguments = "`"$targetPath`""
    $shortcut.WorkingDirectory = "E:\TORQ-CONSOLE"
    $shortcut.IconLocation = $iconPath
    $shortcut.Description = "TORQ Console with Prince Flowers Enhanced Agent"
    $shortcut.WindowStyle = 1

    $shortcut.Save()

    Write-Host "[OK] New shortcut created!"
    Write-Host "[OK] Location: $shortcutPath"
    Write-Host "[OK] Icon: $iconPath"
}

Write-Host ""
Write-Host "========================================"
Write-Host "Done! Press F5 to refresh your desktop."
Write-Host "========================================"
Write-Host ""

# Refresh icon cache
Write-Host "Refreshing icon cache..."
ie4uinit.exe -show

Start-Sleep -Seconds 2
Write-Host "[OK] Icon cache refreshed!"
