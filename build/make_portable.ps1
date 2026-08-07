# Create a portable folder distribution (no installer).
# Run after: npm run build in /web and pip install -e backend + desktop.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "build\output\ShareBox-portable"
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Copy-Item -Recurse -Force (Join-Path $Root "backend\sharebox") (Join-Path $Out "sharebox")
Copy-Item -Recurse -Force (Join-Path $Root "desktop\sharebox_desktop") (Join-Path $Out "sharebox_desktop")

@"
@echo off
set PYTHONPATH=%~dp0
python -m sharebox_desktop
"@ | Set-Content (Join-Path $Out "ShareBox.bat")

@"
# ShareBox portable

1. Install Python 3.12+ and: pip install fastapi uvicorn python-multipart aiofiles watchdog zeroconf qrcode pillow pydantic pydantic-settings pywebview pystray
2. Double-click ShareBox.bat
3. Pair a device from the Control Center

For a standalone .exe, use build_windows.ps1 instead.
"@ | Set-Content (Join-Path $Out "README.txt")

Write-Host "Portable folder: $Out"
