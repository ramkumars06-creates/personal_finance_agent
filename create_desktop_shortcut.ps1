$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "Personal Finance Agent.lnk"

$TargetFile = Join-Path -Path $PSScriptRoot -ChildPath "launch_desktop_app.bat"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "Personal Finance Agent AI Assistant"
$Shortcut.Save()

Write-Host "Desktop shortcut created at: $ShortcutPath"
