# Create Working TORQ Console Shortcut with Icon

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "TORQ Console.lnk"
$iconPath = "E:\TORQ-CONSOLE\torq_console_icon.ico"
$targetPath = "E:\TORQ-CONSOLE\launch_torq_console.bat"

Write-Host "========================================"
Write-Host "Creating TORQ Console Desktop Shortcut"
Write-Host "========================================"
Write-Host ""

# Delete old shortcuts first
$oldShortcuts = Get-ChildItem $desktopPath -Filter "*.lnk" | Where-Object {
    $_.Name -like "*TORQ*Console*"
}

foreach ($oldShortcut in $oldShortcuts) {
    Write-Host "[CLEANUP] Removing old shortcut: $($oldShortcut.Name)"
    Remove-Item $oldShortcut.FullName -Force
}

Write-Host ""

# Verify icon exists
if (-not (Test-Path $iconPath)) {
    Write-Host "[ERROR] Icon file not found at: $iconPath"
    exit 1
}

Write-Host "[OK] Icon found: $iconPath"

# Verify launcher exists
if (-not (Test-Path $targetPath)) {
    Write-Host "[ERROR] Launcher not found at: $targetPath"
    exit 1
}

Write-Host "[OK] Launcher found: $targetPath"
Write-Host ""

# Create the shortcut
$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)

$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = "E:\TORQ-CONSOLE"
$shortcut.IconLocation = $iconPath
$shortcut.Description = "TORQ Console - GPU-Accelerated AI Development Environment"
$shortcut.WindowStyle = 1  # Normal window

$shortcut.Save()

Write-Host "[SUCCESS] Shortcut created!"
Write-Host "  Location: $shortcutPath"
Write-Host "  Icon: $iconPath"
Write-Host "  Target: $targetPath"
Write-Host ""

# Refresh icon cache
Write-Host "Refreshing icon cache..."
ie4uinit.exe -show
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================"
Write-Host "Done! Refreshing desktop..."
Write-Host "========================================"
Write-Host ""

# Force refresh desktop
$code = @"
[DllImport("user32.dll")]
public static extern int SendMessage(IntPtr hWnd, int Msg, int wParam, int lParam);
"@

$type = Add-Type -MemberDefinition $code -Name Win32Utils -Namespace Win32 -PassThru
$HWND_BROADCAST = [IntPtr]0xffff
$WM_SETTINGCHANGE = 0x1a
$type::SendMessage($HWND_BROADCAST, $WM_SETTINGCHANGE, 0, 0) | Out-Null

Write-Host "[OK] Desktop refreshed!"
Write-Host ""
Write-Host "The shortcut is ready to use."
Write-Host "Double-click 'TORQ Console' on your desktop to launch!"
