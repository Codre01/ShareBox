"""Best-effort system tray for ShareBox desktop."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("sharebox.tray")
ASSETS = Path(__file__).resolve().parent / "assets"

# On Linux the tray backend (AppIndicator) shares the GTK main loop that
# pywebview owns, so the icon has to attach to the running loop instead of
# starting a second one on its own thread.
TRAY_NEEDS_RUNNING_LOOP = sys.platform.startswith("linux")


def start_tray(
    *,
    on_open: Callable[[], None],
    on_quit: Callable[[], None],
) -> Any | None:
    """Start the tray icon. Returns the icon so callers can stop it, or None."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        logger.info("pystray/Pillow not installed — tray disabled")
        return None

    def icon_image():
        logo = ASSETS / "sharebox-logo.png"
        if logo.is_file():
            img = Image.open(logo).convert("RGBA")
            return img.resize((64, 64), Image.Resampling.LANCZOS)
        img = Image.new("RGB", (64, 64), color=(22, 24, 38))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((12, 12, 52, 52), radius=10, outline=(145, 132, 217), width=3)
        return img

    menu = pystray.Menu(
        pystray.MenuItem("Open ShareBox", lambda: on_open()),
        pystray.MenuItem("Quit", lambda: on_quit()),
    )
    icon = pystray.Icon("ShareBox", icon_image(), "ShareBox", menu)

    if TRAY_NEEDS_RUNNING_LOOP:
        try:
            icon.run_detached()
            return icon
        except NotImplementedError:
            logger.info("Tray backend has no detached mode — starting its own loop")

    threading.Thread(target=icon.run, name="sharebox-tray", daemon=True).start()
    return icon
