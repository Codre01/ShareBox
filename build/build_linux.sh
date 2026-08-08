#!/usr/bin/env bash
#
# Build a ShareBox .deb for Debian / Ubuntu / Mint.
#
# Usage (from anywhere):
#   ./build/build_linux.sh
#
# Environment overrides:
#   SHAREBOX_VERSION   package version           (default: from desktop/pyproject.toml)
#   SHAREBOX_VENV      build virtualenv path     (default: <repo>/.venv)
#   SHAREBOX_ARCH      dpkg architecture         (default: dpkg --print-architecture)
#   SHAREBOX_MAINTAINER  Maintainer: field
#   SKIP_WEB=1         reuse the existing web build instead of running npm
#
# Output: build/output/sharebox_<version>_<arch>.deb

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT="$ROOT/build/output"
PKGROOT="$ROOT/build/deb-root"
WORK="$ROOT/build/pyi-work"
LINUX_ASSETS="$ROOT/build/linux"
VENV="${SHAREBOX_VENV:-$ROOT/.venv}"
MAINTAINER="${SHAREBOX_MAINTAINER:-ShareBox Contributors <https://github.com/Bolutifebabs8/ShareBox>}"

# Runtime libraries we deliberately do NOT bundle: PyGObject binds to the
# system GTK/WebKit stack, and bundling those pulls in the whole desktop
# theming layer. They are present on any normal desktop install anyway.
DEPENDS="${SHAREBOX_DEPENDS:-python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1, libgtk-3-0, xdg-utils}"
RECOMMENDS="gir1.2-ayatanaappindicator3-0.1"

log() { printf '\033[1;35m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- prerequisites
for tool in dpkg-deb dpkg-architecture fakeroot python3; do
    command -v "$tool" >/dev/null 2>&1 || die "missing '$tool' (apt install dpkg-dev fakeroot)"
done

VERSION="${SHAREBOX_VERSION:-$(
    python3 - <<'PY'
import pathlib, re
text = pathlib.Path("desktop/pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
print(match.group(1) if match else "0.0.0")
PY
)}"
ARCH="${SHAREBOX_ARCH:-$(dpkg --print-architecture)}"
PKGNAME="sharebox_${VERSION}_${ARCH}.deb"

log "Building ShareBox $VERSION for $ARCH"

# ------------------------------------------------------------------ web client
if [ "${SKIP_WEB:-0}" = "1" ]; then
    log "Skipping web build (SKIP_WEB=1)"
    [ -f "$ROOT/backend/sharebox/static/index.html" ] || die "no existing web build to reuse"
else
    command -v npm >/dev/null 2>&1 || die "missing 'npm' (needed to build the web client)"
    log "Building web client"
    (cd "$ROOT/web" && npm install --silent && npm run build)
fi

# ----------------------------------------------------------------- python build
if [ ! -x "$VENV/bin/python" ]; then
    log "Creating build virtualenv at $VENV"
    # --system-site-packages exposes the distro's python3-gi to pywebview.
    python3 -m venv --system-site-packages "$VENV"
fi
PY="$VENV/bin/python"

"$PY" -c "import gi" 2>/dev/null || die \
    "PyGObject not importable. Install it and rebuild the venv with --system-site-packages:
    sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1"

log "Installing Python packages"
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -e "$ROOT/backend"
"$PY" -m pip install --quiet -e "$ROOT/desktop"
"$PY" -m pip install --quiet pyinstaller

# ------------------------------------------------------------------ pyinstaller
log "Running PyInstaller (onedir)"
rm -rf "$PKGROOT" "$OUT/ShareBox" "$WORK"
mkdir -p "$OUT"

# onedir, not onefile: onefile re-extracts to /tmp on every launch, which is
# slow and breaks outright when /tmp is mounted noexec.
# The spec does the work — see build/linux/ShareBox.spec for why it prunes
# the GTK theme data PyInstaller's hooks would otherwise collect.
"$VENV/bin/pyinstaller" \
    --noconfirm \
    --clean \
    --distpath "$OUT" \
    --workpath "$WORK" \
    "$LINUX_ASSETS/ShareBox.spec"

[ -x "$OUT/ShareBox/ShareBox" ] || die "PyInstaller did not produce $OUT/ShareBox/ShareBox"

# ------------------------------------------------------------------- deb layout
log "Assembling package tree"
install -d "$PKGROOT/DEBIAN" \
           "$PKGROOT/opt/sharebox" \
           "$PKGROOT/usr/bin" \
           "$PKGROOT/usr/share/applications" \
           "$PKGROOT/usr/share/doc/sharebox"

cp -a "$OUT/ShareBox/." "$PKGROOT/opt/sharebox/"
ln -sf /opt/sharebox/ShareBox "$PKGROOT/usr/bin/sharebox"
install -m 644 "$LINUX_ASSETS/sharebox.desktop" "$PKGROOT/usr/share/applications/sharebox.desktop"

log "Rendering icons"
"$PY" - "$ROOT/desktop/sharebox_desktop/assets/sharebox-logo.png" "$PKGROOT" <<'PY'
import sys, pathlib
from PIL import Image

source, pkgroot = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
logo = Image.open(source).convert("RGBA")
for size in (16, 24, 32, 48, 64, 128, 256):
    target = pkgroot / f"usr/share/icons/hicolor/{size}x{size}/apps"
    target.mkdir(parents=True, exist_ok=True)
    logo.resize((size, size), Image.Resampling.LANCZOS).save(target / "sharebox.png")
print(f"  icons written from {source.name} ({logo.width}x{logo.height})")
PY

install -m 644 "$ROOT/LICENSE" "$PKGROOT/usr/share/doc/sharebox/copyright"
printf 'sharebox (%s) unstable; urgency=low\n\n  * See https://github.com/Bolutifebabs8/ShareBox/releases\n\n -- %s  %s\n' \
    "$VERSION" "$MAINTAINER" "$(date -R)" \
    | gzip -9n > "$PKGROOT/usr/share/doc/sharebox/changelog.Debian.gz"

INSTALLED_SIZE="$(du -sk "$PKGROOT" | cut -f1)"
sed -e "s|@VERSION@|$VERSION|" \
    -e "s|@ARCH@|$ARCH|" \
    -e "s|@MAINTAINER@|$MAINTAINER|" \
    -e "s|@INSTALLED_SIZE@|$INSTALLED_SIZE|" \
    -e "s|@DEPENDS@|$DEPENDS|" \
    "$LINUX_ASSETS/control.in" > "$PKGROOT/DEBIAN/control"
printf 'Recommends: %s\n' "$RECOMMENDS" >> "$PKGROOT/DEBIAN/control"

install -m 755 "$LINUX_ASSETS/postinst" "$PKGROOT/DEBIAN/postinst"
install -m 755 "$LINUX_ASSETS/postrm" "$PKGROOT/DEBIAN/postrm"

# dpkg refuses group/other-writable files in a package.
chmod -R go-w "$PKGROOT"

# ----------------------------------------------------------------------- build
log "Building $PKGNAME"
fakeroot dpkg-deb --build --root-owner-group "$PKGROOT" "$OUT/$PKGNAME" >/dev/null

if command -v lintian >/dev/null 2>&1; then
    log "lintian (informational)"
    lintian --no-tag-display-limit "$OUT/$PKGNAME" || true
fi

log "Done: $OUT/$PKGNAME ($(du -h "$OUT/$PKGNAME" | cut -f1))"
echo
echo "  Install:    sudo apt install $OUT/$PKGNAME"
echo "  Uninstall:  sudo apt remove sharebox"
