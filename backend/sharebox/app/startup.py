"""Platform dispatch for the launch-at-startup toggle."""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger("sharebox.startup")


def supports_launch_at_startup() -> bool:
    """True when this platform has a launch-at-startup implementation."""
    return sys.platform == "win32" or sys.platform.startswith("linux")


def set_launch_at_startup(enabled: bool, command: str | None = None) -> None:
    if sys.platform == "win32":
        from sharebox.app.startup_windows import set_launch_at_startup as impl
    elif sys.platform.startswith("linux"):
        from sharebox.app.startup_linux import set_launch_at_startup as impl
    else:
        logger.info("Launch-at-startup is not implemented for %s", sys.platform)
        return
    impl(enabled, command)
