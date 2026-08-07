# Portable / developer run notes (Windows)

## Dev mode (recommended while building)

```powershell
cd "C:\Users\user\Documents\Personal Projects\ShareBox"
.\.venv\Scripts\Activate.ps1
cd web; npm run build; cd ..
python -m sharebox_desktop
```

Headless API only:

```powershell
uvicorn sharebox.app.main:app --host 0.0.0.0 --port 8765
```

## Packaged artifact

```powershell
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
```

Output: `build\output\ShareBox.exe` (onefile). Requires WebView2 (preinstalled on Windows 10/11).

## First-run

1. Launch ShareBox
2. Confirm shared folder (default `~\ShareBox`)
3. Click **Pair new device** and scan QR from a phone on the same Wi‑Fi
4. Browse / upload / download

## Security

V1 uses HTTP on the LAN with high-entropy device tokens. See ADR-003 and the README security note.
