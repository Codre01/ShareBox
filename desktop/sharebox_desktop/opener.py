"""Open files, folders and URLs in the user's desktop environment."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("sharebox.opener")


def open_path(path: Path) -> None:
    """Reveal a file or folder using the platform's default handler."""
    target = str(path)
    if sys.platform == "win32":
        os.startfile(target)  # type: ignore[attr-defined]
        return
    launcher = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen(
            [launcher, target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Could not open {target}: {launcher} is not installed") from exc


def open_url(url: str) -> None:
    """Open an http(s) URL in the default browser."""
    if urlparse(url).scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are allowed")
    webbrowser.open(url)
