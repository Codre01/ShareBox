# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the ShareBox Linux build.

PyInstaller's GObject hooks sweep in the *build machine's* entire desktop
theming layer — every installed cursor and GTK theme, around 1.5 GB, and
different on every machine. The package Depends: on the system GTK stack,
so that data is dropped here: it keeps the .deb a sane size and, more
importantly, makes the build reproducible instead of a snapshot of whatever
themes the packager happened to have installed.
"""

import os

from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

# Provided at runtime by the packages listed in Depends: (libgtk-3-0,
# gir1.2-webkit2-4.1, ...). Bundling them adds ~1.5 GB and overrides the
# user's own desktop theme with the packager's.
EXCLUDED_DATA_DIRS = ("share/icons", "share/themes")

# The numeric stack arrives through an optional import chain; ShareBox never
# does array maths. The `excludes` below drop the Python packages, this drops
# the shared libraries they drag along.
EXCLUDED_BINARY_PREFIXES = ("liblapack", "libblas", "libgfortran", "libquadmath")


a = Analysis(
    [os.path.join(ROOT, "desktop", "sharebox_desktop", "__main__.py")],
    pathex=[os.path.join(ROOT, "backend"), os.path.join(ROOT, "desktop")],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "backend", "sharebox", "static"), "sharebox/static"),
        (os.path.join(ROOT, "backend", "sharebox", "host"), "sharebox/host"),
        (os.path.join(ROOT, "desktop", "sharebox_desktop", "assets"), "sharebox_desktop/assets"),
    ],
    hiddenimports=[
        # pywebview and pystray pick their backend at runtime, so the static
        # analysis never sees these imports.
        "webview.platforms.gtk",
        "pystray._appindicator",
        "pystray._xorg",
        *collect_submodules("uvicorn"),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
    ],
    noarchive=False,
    optimize=0,
)

a.datas = [
    entry
    for entry in a.datas
    if not entry[0].replace(os.sep, "/").startswith(EXCLUDED_DATA_DIRS)
]
a.binaries = [
    entry
    for entry in a.binaries
    if not os.path.basename(entry[0]).startswith(EXCLUDED_BINARY_PREFIXES)
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ShareBox",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ShareBox",
)
