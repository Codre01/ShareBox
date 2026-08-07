# ShareBox

Local-network file sharing between your computer and nearby devices. No cloud, no cables, no phone app — just a folder on your PC and a browser on your phone.

## Status

Windows V1 in active development. See [docs/ShareBox Product Documentation.md](docs/ShareBox%20Product%20Documentation.md) for the full product and engineering specification.

## Architecture

| Layer | Stack |
|-------|--------|
| Backend | Python 3.12 + FastAPI |
| Web client | TypeScript + Vite + React (served by the host) |
| Desktop | PyWebView Control Center + system tray |
| Persistence | SQLite + JSON config in OS app-data |

## Development

### Prerequisites

- Python 3.12+
- Node.js 20+

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
uvicorn sharebox.app.main:app --host 127.0.0.1 --port 8765 --reload
```

### Web client

```bash
cd web
npm install
npm run dev                     # http://127.0.0.1:5173 (proxies API)
npm run build                   # outputs into backend/sharebox/static
```

### Desktop Control Center

```bash
cd desktop
pip install -e .
python -m sharebox_desktop
```

### Tests

```bash
cd backend
pytest
```

## Security note (V1)

ShareBox V1 uses HTTP on the local LAN with high-entropy device credentials. This protects against casual unauthorized access but does **not** provide confidentiality against a capable attacker on the same network. Do not use ShareBox on untrusted networks for sensitive files.

Host administration (pairing approval, device revoke, settings) is restricted to the Control Center on the host computer (loopback). See [docs/security.md](docs/security.md) for the full hardening notes.

## License

MIT — see [LICENSE](LICENSE).
