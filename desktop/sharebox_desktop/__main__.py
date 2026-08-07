from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path

logger = logging.getLogger("sharebox.desktop")


def _ensure_path() -> None:
    root = Path(__file__).resolve().parents[2]
    backend = root / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    if str(Path(__file__).resolve().parents[1]) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    _ensure_path()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

    from sharebox.app.config import ConfigStore
    from sharebox_desktop.app import run_desktop

    cfg = ConfigStore()
    os.environ.setdefault("SHAREBOX_PORT", str(cfg.config.port))
    run_desktop()


if __name__ == "__main__":
    main()
