# ADR-001: Desktop UI framework

## Status

Accepted

## Context

ShareBox needs a cross-platform desktop shell with tray support, native folder dialogs, and a Control Center UI already prototyped in HTML (Nocturne). Spec §70 forbids choosing Electron merely because it is familiar.

## Decision

Use **PyWebView** to host the Control Center HTML/JS UI, with the FastAPI backend running in-process or as a managed sibling thread/process in the same Python runtime.

## Alternatives considered

- **Electron / Tauri**: heavier dual-runtime (Node/Rust + Python sidecar).
- **Native Qt/Tk**: would require reimplementing the Nocturne Control Center from scratch.

## Consequences

- Single language (Python) for host + backend lifecycle.
- Small Chromium/Edge WebView2 dependency on Windows (system WebView2).
- Desktop UI shares design tokens with the web client.
