"""Linux launch-at-startup helper via the XDG autostart spec."""

from __future__ import annotations

import logging
import os
import shlex
import sys
from pathlib import Path

logger = logging.getLogger("sharebox.startup")

DESKTOP_FILE_NAME = "sharebox.desktop"


def autostart_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "autostart"


def _default_command() -> str:
    # A packaged build is a single executable; a source checkout needs the
    # interpreter plus the module.
    if getattr(sys, "frozen", False):
        return shlex.quote(sys.executable)
    return f"{shlex.quote(sys.executable)} -m sharebox_desktop"


def set_launch_at_startup(enabled: bool, command: str | None = None) -> None:
    path = autostart_dir() / DESKTOP_FILE_NAME
    if not enabled:
        try:
            path.unlink()
            logger.info("Disabled launch at startup")
        except FileNotFoundError:
            pass
        return

    entry = "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            "Name=ShareBox",
            "Comment=Share files with nearby devices over Wi-Fi",
            f"Exec={command or _default_command()}",
            "Icon=sharebox",
            "Terminal=false",
            "X-GNOME-Autostart-enabled=true",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(entry, encoding="utf-8")
    logger.info("Enabled launch at startup: %s", path)
