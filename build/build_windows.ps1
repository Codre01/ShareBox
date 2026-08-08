# Build ShareBox Windows artifacts (dev / CI helper)
# Usage (from repo root, with venv active):
#   powershell -File build\build_windows.ps1
#   powershell -File build\build_windows.ps1 -SkipShortcut   # no Desktop shortcut
#
# The shortcut is a convenience for developers building locally. It is skipped
# automatically when $env:CI is set, since a build agent has no desktop to put
# it on.

param(
  [switch]$SkipShortcut
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Building web client"
Push-Location web
npm install
npm run build
Pop-Location

Write-Host "==> Ensuring Python packages"
Push-Location backend
python -m pip install -e ".[dev]"
Pop-Location
Push-Location desktop
python -m pip install -e "."
python -m pip install pystray pillow pyinstaller
Pop-Location

$Out = Join-Path $Root "build\output"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Write-Host "==> PyInstaller onefile ShareBox"
$entry = Join-Path $Root "desktop\sharebox_desktop\__main__.py"
$icon = Join-Path $Root "desktop\sharebox_desktop\assets\sharebox.ico"
if (-not (Test-Path $icon)) {
  throw "Missing app icon: $icon"
}
# Unlock previous artifact if a running ShareBox still has it open.
Get-Process -Name ShareBox -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

pyinstaller `
  --noconfirm `
  --clean `
  --name ShareBox `
  --onefile `
  --windowed `
  --icon $icon `
  --paths (Join-Path $Root "backend") `
  --paths (Join-Path $Root "desktop") `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\control_center.html');sharebox_desktop" `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\control_center.js');sharebox_desktop" `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\nocturne.css');sharebox_desktop" `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\assets');sharebox_desktop/assets" `
  --add-data "$(Join-Path $Root 'backend\sharebox\static');sharebox/static" `
  --add-data "$(Join-Path $Root 'backend\sharebox\host');sharebox/host" `
  --distpath $Out `
  --workpath (Join-Path $Root "build\pyi-work") `
  --specpath (Join-Path $Root "build") `
  $entry
if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with exit code $LASTEXITCODE (is ShareBox.exe still running?)"
}

$exe = Join-Path $Out "ShareBox.exe"
if (-not (Test-Path $exe)) {
  throw "Build finished but ShareBox.exe was not found at $exe"
}

# Portable build: create a Desktop shortcut so the app is easy to launch.
# (There is no Windows installer yet — this is plug-and-play .exe distribution.)
if ($SkipShortcut -or $env:CI) {
  Write-Host "Skipping Desktop shortcut"
} else {
  $desktop = [Environment]::GetFolderPath("Desktop")
  $shortcutPath = Join-Path $desktop "ShareBox.lnk"
  $shell = New-Object -ComObject WScript.Shell
  $shortcut = $shell.CreateShortcut($shortcutPath)
  $shortcut.TargetPath = $exe
  $shortcut.WorkingDirectory = $Out
  $shortcut.IconLocation = "$exe,0"
  $shortcut.Description = "ShareBox"
  $shortcut.Save()
  Write-Host "Desktop shortcut: $shortcutPath"
}

Write-Host "Artifacts in $Out"
Get-ChildItem $Out
