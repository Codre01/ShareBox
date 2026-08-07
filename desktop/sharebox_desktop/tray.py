"""Best-effort system tray for ShareBox desktop."""

from __future__ import annotations

import logging
import threading
from typing import Callable

logger = logging.getLogger("sharebox.tray")


def start_tray(
    *,
    on_open: Callable[[], None],
    on_quit: Callable[[], None],
) -> None:
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        logger.info("pystray/Pillow not installed — tray disabled")
        return

    def icon_image():
        img = Image.new("RGB", (64, 64), color=(22, 24, 38))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((12, 12, 52, 52), radius=10, outline=(145, 132, 217), width=3)
        return img

    menu = pystray.Menu(
        pystray.MenuItem("Open ShareBox", lambda: on_open()),
        pystray.MenuItem("Quit", lambda: on_quit()),
    )
    icon = pystray.Icon("ShareBox", icon_image(), "ShareBox", menu)

    def run() -> None:
        icon.run()

    threading.Thread(target=run, name="sharebox-tray", daemon=True).start()
