# Running and packaging ShareBox on Linux

Covers Debian, Ubuntu, Linux Mint and derivatives. Other distros can run from
source; only the `.deb` is Debian-specific.

## Install the package

```bash
sudo apt install ./sharebox_0.1.0_amd64.deb
```

`apt install ./file.deb` (with the `./`) pulls in the GTK dependencies
automatically. `dpkg -i` does not — if you use it, follow with
`sudo apt --fix-broken install`.

Then launch **ShareBox** from your application menu, or run `sharebox` in a
terminal.

| | |
|---|---|
| App | `/opt/sharebox/` |
| Command | `/usr/bin/sharebox` |
| Desktop entry | `/usr/share/applications/sharebox.desktop` |
| Config + database | `~/.config/sharebox/` |
| Default shared folder | `~/ShareBox` |

Uninstall with `sudo apt remove sharebox`. Your config and shared folder are
deliberately left in place; delete `~/.config/sharebox` and `~/ShareBox`
yourself if you want them gone.

## Requirements

The package depends on the system GTK/WebKit stack rather than bundling it, so
your own desktop theme is used and the download stays reasonable:

```
python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1, libgtk-3-0, xdg-utils
```

`gir1.2-ayatanaappindicator3-0.1` is *recommended* rather than required — without
it the app runs fine but has no system-tray icon, so closing the window quits
ShareBox instead of leaving it running in the background.

## Dev mode (running from source)

```bash
sudo apt install python3-venv python3-pip python3-gi \
    gir1.2-gtk-3.0 gir1.2-webkit2-4.1 gir1.2-ayatanaappindicator3-0.1

python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e "./backend[dev]"
.venv/bin/pip install -e "./desktop"
(cd web && npm install && npm run build)
.venv/bin/python -m sharebox_desktop
```

The venv **must** be created with `--system-site-packages`; pywebview's GTK
backend and pystray's tray backend both import the distro's `python3-gi`, which
a sealed venv cannot see.

Headless API only (no Control Center window):

```bash
.venv/bin/uvicorn sharebox.app.main:app --host 0.0.0.0 --port 8765
```

## Building the .deb

```bash
./build/build_linux.sh
```

Output: `build/output/sharebox_<version>_<arch>.deb`.

| Variable | Purpose |
|----------|---------|
| `SKIP_WEB=1` | Reuse the existing web build instead of running npm |
| `SHAREBOX_VERSION` | Override the package version |
| `SHAREBOX_VENV` | Use a different build virtualenv |
| `SHAREBOX_ARCH` | Cross-label the architecture |

The build is a PyInstaller **onedir** bundle (not onefile — onefile re-extracts
to `/tmp` on every launch, which is slow and fails outright when `/tmp` is
mounted `noexec`) plus `dpkg-deb`.

### Why there is a spec file

`build/linux/ShareBox.spec` prunes what PyInstaller's GObject hooks collect. Left
alone, those hooks copy **every cursor and GTK theme installed on the build
machine** — about 1.5 GB, and different on every packager's machine. The spec
drops `share/icons` and `share/themes` (the system provides them) along with an
unused numpy/LAPACK stack that arrives through an optional import chain.

If you change dependencies and the package suddenly balloons, check what landed
in `build/output/ShareBox/_internal` before assuming the spec is wrong:

```bash
du -sh build/output/ShareBox/_internal/* | sort -rh | head
```

## Troubleshooting

**App menu entry missing after install** — some desktops cache the menu; log out
and back in, or run `update-desktop-database ~/.local/share/applications`.

**No tray icon** — install `gir1.2-ayatanaappindicator3-0.1`. GNOME also needs an
AppIndicator extension; without one the icon is hidden even when present.

**Window is blank** — the WebKit renderer can fail under some GPU drivers. Run
`sharebox` from a terminal and check for WebKit errors; `WEBKIT_DISABLE_COMPOSITING_MODE=1 sharebox`
is the usual workaround.

**`Failed to load module "xapp-gtk3-module"` on Mint** — harmless. The bundled
GTK cannot load Mint's XApp integration module; it only affects desktop-specific
menu decoration, not ShareBox itself.

**Phone can't reach the host** — the port must be open:
`sudo ufw allow 8765/tcp`. See [troubleshooting.md](troubleshooting.md) for
router-level causes.

## Security

Same as every platform: HTTP on the LAN with high-entropy device tokens. See
[security.md](security.md) and ADR-003.
