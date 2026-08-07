# Build ShareBox Windows artifacts (dev / CI helper)
# Usage (from repo root, with venv active):
#   powershell -File build\build_windows.ps1

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
pyinstaller `
  --noconfirm `
  --clean `
  --name ShareBox `
  --onefile `
  --windowed `
  --paths (Join-Path $Root "backend") `
  --paths (Join-Path $Root "desktop") `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\control_center.html');sharebox_desktop" `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\control_center.js');sharebox_desktop" `
  --add-data "$(Join-Path $Root 'desktop\sharebox_desktop\nocturne.css');sharebox_desktop" `
  --add-data "$(Join-Path $Root 'backend\sharebox\static');sharebox/static" `
  --distpath $Out `
  --workpath (Join-Path $Root "build\pyi-work") `
  --specpath (Join-Path $Root "build") `
  $entry

Write-Host "Artifacts in $Out"
Get-ChildItem $Out
