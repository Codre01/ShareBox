"""Windows launch-at-startup helper via current-user Run key."""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger("sharebox.startup")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "ShareBox"


def set_launch_at_startup(enabled: bool, command: str | None = None) -> None:
    if sys.platform != "win32":
        logger.info("Launch-at-startup is only implemented for Windows in V1")
        return
    try:
        import winreg
    except ImportError:
        return

    cmd = command or f'"{sys.executable}" -m sharebox_desktop'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, cmd)
            logger.info("Enabled launch at startup")
        else:
            try:
                winreg.DeleteValue(key, VALUE_NAME)
                logger.info("Disabled launch at startup")
            except FileNotFoundError:
                pass
