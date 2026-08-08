# Contributing to ShareBox

Thanks for helping. ShareBox is intentionally small: a local host app + a browser client. Contributions that keep that story clear are especially welcome.

## Ways to help

| Area | Examples |
|------|----------|
| **Bugs** | Reproduce, open an issue with steps + OS + logs |
| **Features** | Open an issue first for anything larger than a small UX tweak |
| **macOS / Linux** | Desktop shell (tray, WebView), packaging (`.app`, AppImage), docs |
| **Docs** | User guide clarity, troubleshooting, translations later |
| **Tests** | Backend pytest coverage for pairing, files, auth edges |
| **Security** | See [docs/security.md](docs/security.md) — prefer responsible disclosure |

## Development setup

Prerequisites: **Python 3.12+**, **Node.js 20+**, Git.

### Windows

```powershell
git clone https://github.com/Bolutifebabs8/ShareBox.git
cd ShareBox
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".\backend[dev]"
pip install -e ".\desktop"
cd web
npm install
npm run build
cd ..
python -m sharebox_desktop
```

### Linux (Debian / Ubuntu / Mint)

The Control Center uses pywebview's GTK backend and the tray uses AppIndicator,
so both come from system packages rather than pip:

```bash
sudo apt install python3-venv python3-pip python3-gi \
    gir1.2-gtk-3.0 gir1.2-webkit2-4.1 gir1.2-ayatanaappindicator3-0.1

git clone https://github.com/Bolutifebabs8/ShareBox.git
cd ShareBox
# --system-site-packages lets the venv see python3-gi; pip installs still win.
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e "./backend[dev]"
.venv/bin/pip install -e "./desktop"
(cd web && npm install && npm run build)
.venv/bin/python -m sharebox_desktop
```

Building `PyGObject` from pip instead (other distros) needs
`libgirepository1.0-dev` and `libcairo2-dev`; then `pip install -e "./desktop[linux]"`.

### Useful commands

| Task | Command |
|------|---------|
| API only (hot reload) | `uvicorn sharebox.app.main:app --host 127.0.0.1 --port 8765 --reload` (from repo with `PYTHONPATH` / editable install) |
| Web UI with Vite | `cd web; npm run dev` → http://127.0.0.1:5173 |
| Rebuild web into backend | `cd web; npm run build` |
| Tests | `cd backend; pytest` |
| Windows exe | `powershell -ExecutionPolicy Bypass -File build\build_windows.ps1` |

App data (config, SQLite) lives under the OS app-data directory: `%LOCALAPPDATA%\ShareBox`
on Windows, `~/.config/sharebox` on Linux.

## Project map

- `backend/sharebox/app/` — API, auth/pairing, files, clipboard, mDNS, security helpers  
- `backend/sharebox/host/` — Control Center HTML/JS served at `/host` (loopback-only)  
- `desktop/sharebox_desktop/` — window, tray, startup helper  
- `web/src/` — phone/browser client  
- `docs/adr/` — architecture decisions  

## Pull requests

1. Fork and create a branch: `git checkout -b fix/short-name` or `feat/short-name`.
2. Keep PRs focused — one concern per PR when possible.
3. Add or update tests for backend behavior changes.
4. Run `pytest` before opening the PR.
5. Fill in the PR template: what changed, how to test.

### Style

- Match existing code style; prefer small, readable diffs.
- Don’t commit secrets, local `.db` files, or `build/output/*.exe`.
- Don’t expand scope into unrelated refactors.

## Good first issues / high-impact work

- Improve troubleshooting docs from real support questions  
- Harden packaging / code signing notes for Windows releases  
- **macOS** Control Center + tray + notarization path  
- **Linux** WebView backend + AppImage  
- Pairing / upload UX polish on mobile browsers  
- Automated CI: lint + pytest on PRs  

## Code of collaboration

Be respectful. Assume good intent. Prefer concrete repro steps over vague “it doesn’t work.” Maintainers may ask to split large PRs.

## License

By contributing, you agree your contributions are licensed under the MIT License ([LICENSE](LICENSE)).
