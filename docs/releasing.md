# Publishing a Windows release

For maintainers shipping a new version people can download from GitHub.

## 1. Build

```powershell
.\.venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
```

Artifact: `build\output\ShareBox.exe` (gitignored — do not commit).

## 2. Smoke-test

Walk [acceptance-checklist.md](acceptance-checklist.md) on a real LAN with a phone.

## 3. Tag and release

```powershell
git tag v0.1.0
git push origin v0.1.0

gh release create v0.1.0 `
  "build\output\ShareBox.exe" `
  --title "ShareBox v0.1.0" `
  --notes-file docs\release-notes-template.md
```

Or draft notes in the GitHub UI and attach `ShareBox.exe` as a binary asset.

## 4. Verify

Open https://github.com/Bolutifebabs8/ShareBox/releases/latest and confirm the Download button works for a fresh machine.
