from __future__ import annotations

import logging
import socket
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
import webview

from sharebox.app.config import ConfigStore
from sharebox.app.main import create_app
from sharebox_desktop.startup import set_launch_at_startup
from sharebox_desktop.tray import start_tray

logger = logging.getLogger("sharebox.desktop")
UI_DIR = Path(__file__).resolve().parent


def _wait_port(host: str, port: int, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


class Api:
    def __init__(self, config: ConfigStore, window_holder: dict) -> None:
        self.config = config
        self.window_holder = window_holder

    def pick_folder(self) -> str | None:
        window = self.window_holder.get("window")
        if not window:
            return None
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            return result[0]
        return None

    def open_folder(self, path: str) -> None:
        import os

        os.startfile(path)  # type: ignore[attr-defined]

    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    def set_startup(self, enabled: bool) -> None:
        set_launch_at_startup(enabled)
        self.config.update(launch_at_startup=enabled)


def run_desktop() -> None:
    config = ConfigStore()
    port = config.config.port
    app = create_app()

    def serve() -> None:
        uvicorn.run(app, host=config.config.bind_host, port=port, log_level="info")

    thread = threading.Thread(target=serve, name="sharebox-uvicorn", daemon=True)
    thread.start()
    if not _wait_port("127.0.0.1", port):
        logger.error("Backend failed to start on port %s", port)
        return

    if config.config.launch_at_startup:
        set_launch_at_startup(True)

    window_holder: dict = {}
    api = Api(config, window_holder)
    ui = (UI_DIR / "control_center.html").as_uri()
    window = webview.create_window(
        "ShareBox",
        url=ui,
        js_api=api,
        width=1040,
        height=720,
        background_color="#161826",
    )
    window_holder["window"] = window

    def on_shown() -> None:
        window.evaluate_js(f"window.__SHAREBOX_API__ = 'http://127.0.0.1:{port}';")

    def show_window() -> None:
        try:
            window.show()
            window.restore()
        except Exception:
            logger.exception("Could not show window")

    def quit_app() -> None:
        try:
            window.destroy()
        except Exception:
            pass

    window.events.shown += on_shown
    start_tray(on_open=show_window, on_quit=quit_app)
    webview.start(debug=bool(config.config.debug))
