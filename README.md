# ShareBox

**Share files between your PC and nearby phones — over Wi‑Fi. No cloud. No cables. No phone app.**

Your computer runs ShareBox. Everyone else just opens a browser.

---

## Download

### Windows

| | |
|---|---|
| **Get the app** | [**Download ShareBox.exe**](https://github.com/Bolutifebabs8/ShareBox/releases/latest) |
| **Requirements** | Windows 10/11 (WebView2 is usually already installed) |
| **Install?** | No installer — download, double‑click, run |

### Linux (Debian / Ubuntu / Mint)

| | |
|---|---|
| **Get the app** | [**Download sharebox_*.deb**](https://github.com/Bolutifebabs8/ShareBox/releases/latest) |
| **Requirements** | A GTK desktop; dependencies install automatically |
| **Install** | `sudo apt install ./sharebox_0.1.0_amd64.deb` |

Keep the `./` — it lets apt resolve the GTK dependencies. Then launch **ShareBox**
from your application menu or run `sharebox`. Details and troubleshooting:
**[docs/linux-run.md](docs/linux-run.md)**.

### Quick start (for people who just want to use it)

1. Download **ShareBox.exe** (Windows) or **sharebox_*.deb** (Linux) from the [latest release](https://github.com/Bolutifebabs8/ShareBox/releases/latest).
2. Windows: double‑click it. Windows may warn about an unknown app — choose **More info → Run anyway** (normal for new open‑source apps that aren’t code‑signed yet). Linux: `sudo apt install ./sharebox_*.deb`, then launch ShareBox from your app menu.
3. ShareBox opens a Control Center window and shares a folder (default: `Documents\ShareBox` or `~/ShareBox`).
4. In Control Center, click **Pair new device**. On a phone, scan the QR code; on another PC, click **Copy link** and open that URL in a browser (same Wi‑Fi).
5. Approve the device on the host PC, give it a name, then browse / upload / download in the browser.

Full walkthrough, tips, and “what if it doesn’t work”: **[docs/user-guide.md](docs/user-guide.md)** · **[docs/troubleshooting.md](docs/troubleshooting.md)**

> **macOS hosts:** not packaged yet. Phones on any OS already work via the browser once a Windows or Linux host is running. Help welcome — see [Contributing](#for-contributors).

---

## How it works

```text
┌─────────────────────────┐         same Wi‑Fi          ┌──────────────────┐
│  Your PC (ShareBox)     │ ◄──────────────────────────► │ Phone / tablet   │
│  • Control Center       │                              │ browser only     │
│  • Shared folder        │                              │ (no app install) │
│  • Local server :8765   │                              └──────────────────┘
└─────────────────────────┘
```

- Files stay on your computer. Nothing is uploaded to the internet.
- Devices must be **paired and approved** once; you can rename or revoke them later.
- Clipboard snippets can be shared among trusted devices (capped list).

**Security note (V1):** traffic is HTTP on your LAN with strong device tokens. Fine for home/trusted networks — not for hostile public Wi‑Fi with sensitive files. Details: [docs/security.md](docs/security.md).

---

## Repository layout

| Path | What it is |
|------|------------|
| [`backend/`](backend/) | FastAPI server, pairing, files, clipboard, SQLite |
| [`desktop/`](desktop/) | Control Center (PyWebView) + tray, Windows and Linux |
| [`web/`](web/) | React client served to phones/browsers |
| [`build/`](build/) | Packaging: `build_windows.ps1`, `build_linux.sh`, `linux/` deb assets |
| [`docs/`](docs/) | User guide, troubleshooting, ADRs, product spec |
| [`design/`](design/) | UI / design references |

---

## For contributors

Want to suggest features, fix bugs, or help with **macOS** packaging? Start here:

1. Read **[CONTRIBUTING.md](CONTRIBUTING.md)** — setup, workflow, good first areas.
2. Skim **[docs/README.md](docs/README.md)** for the doc map and architecture notes.
3. Open an [issue](https://github.com/Bolutifebabs8/ShareBox/issues) (bug or feature) before large changes when you can.

```powershell
git clone https://github.com/Bolutifebabs8/ShareBox.git
cd ShareBox
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".\backend[dev]"
pip install -e ".\desktop"
cd web; npm install; npm run build; cd ..
python -m sharebox_desktop
```

On Linux the setup differs slightly (system GTK packages, `--system-site-packages` venv) — see [CONTRIBUTING.md](CONTRIBUTING.md) or [docs/linux-run.md](docs/linux-run.md).

Tests: `cd backend; pytest`

Build Windows exe: `powershell -ExecutionPolicy Bypass -File build\build_windows.ps1`

Build Linux .deb: `./build/build_linux.sh`

---

## License

MIT — see [LICENSE](LICENSE). Use it, share it, fork it.
