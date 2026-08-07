# ADR-006: Windows packaging

## Status

Accepted

## Decision

Package Windows V1 with **PyInstaller** onefile (and optional portable folder) via `build/build_windows.ps1`. MSI/installer polish can follow once the onefile artifact is validated.

## Consequences

- Larger binary than a native compile, but single-artifact distribution for contributors.
- WebView2 runtime must be present on the host (standard on Windows 10/11).
