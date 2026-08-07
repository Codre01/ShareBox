from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger("sharebox.watcher")


class _Handler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory and event.event_type == "modified":
            return
        self.callback(event.event_type)


class FolderWatcher:
    def __init__(self, on_change: Callable[[str], None]) -> None:
        self.on_change = on_change
        self._observer: Observer | None = None
        self._path: Path | None = None
        self._lock = threading.Lock()

    def watch(self, path: Path) -> None:
        with self._lock:
            self.stop_locked()
            self._path = path
            handler = _Handler(self.on_change)
            self._observer = Observer()
            self._observer.schedule(handler, str(path), recursive=True)
            self._observer.daemon = True
            self._observer.start()
            logger.info("Watching %s", path)

    def stop(self) -> None:
        with self._lock:
            self.stop_locked()

    def stop_locked(self) -> None:
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=2)
            except Exception:
                logger.exception("Error stopping watcher")
            self._observer = None
