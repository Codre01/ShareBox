from __future__ import annotations

import logging
import socket
import threading
import time
from pathlib import Path

import uvicorn
import webview

from sharebox.app.config import ConfigStore
from sharebox.app.main import create_app
from sharebox.app.network import list_lan_addresses
from sharebox.app.tls import CertificateStore
from sharebox_desktop import opener
from sharebox_desktop.startup import set_launch_at_startup
from sharebox_desktop.tray import TRAY_NEEDS_RUNNING_LOOP, start_tray

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
        target = Path(path).resolve()
        shared = Path(self.config.config.shared_folder).resolve()
        try:
            target.relative_to(shared)
        except ValueError:
            # Allow opening the shared root itself only.
            if target != shared:
                raise ValueError("Folder is outside the ShareBox shared folder")
        opener.open_path(target)

    def open_url(self, url: str) -> None:
        opener.open_url(url)

    def set_startup(self, enabled: bool) -> None:
        set_launch_at_startup(enabled)
        self.config.update(launch_at_startup=enabled)


def run_desktop() -> None:
    config = ConfigStore()
    port = config.config.port
    use_https = config.config.use_https
    app = create_app()

    ssl_kwargs: dict = {}
    if use_https:
        certs = CertificateStore(config.app_data_dir)
        paths = certs.ensure(list_lan_addresses(), config.config.host_name)
        ssl_kwargs = {
            "ssl_certfile": str(paths.certificate),
            "ssl_keyfile": str(paths.key),
        }

    def serve() -> None:
        uvicorn.run(
            app,
            host=config.config.bind_host,
            port=port,
            log_level="info",
            **ssl_kwargs,
        )

    threading.Thread(target=serve, name="sharebox-uvicorn", daemon=True).start()

    # The Control Center talks to a loopback-only plain-HTTP listener. Pointing
    # the WebView at the HTTPS one instead would mean teaching it to trust a
    # self-signed certificate, which WebView2 and WebKitGTK each refuse
    # differently. Same app object, so both listeners share all state.
    ui_port = port
    if use_https:
        ui_port = config.effective_control_port()

        def serve_control() -> None:
            uvicorn.run(app, host="127.0.0.1", port=ui_port, log_level="warning")

        threading.Thread(target=serve_control, name="sharebox-uvicorn-ui", daemon=True).start()

    if not _wait_port("127.0.0.1", ui_port):
        logger.error("Backend failed to start on port %s", ui_port)
        return

    if config.config.launch_at_startup:
        set_launch_at_startup(True)

    window_holder: dict = {}
    api = Api(config, window_holder)
    # Same-origin with the API — avoids file:// CORS preflight failures in WebView2.
    ui = f"http://127.0.0.1:{ui_port}/host/control_center.html"
    window = webview.create_window(
        "ShareBox",
        url=ui,
        js_api=api,
        width=1040,
        height=720,
        background_color="#161826",
    )
    window_holder["window"] = window

    tray_holder: dict = {}

    def show_window() -> None:
        try:
            window.show()
            window.restore()
        except Exception:
            logger.exception("Could not show window")

    def quit_app() -> None:
        icon = tray_holder.pop("icon", None)
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                logger.exception("Could not stop tray icon")
        try:
            window.destroy()
        except Exception:
            pass

    def on_shown() -> None:
        # Empty base = same origin (/api/v1/...)
        window.evaluate_js("window.__SHAREBOX_API__ = '';")
        if TRAY_NEEDS_RUNNING_LOOP and "icon" not in tray_holder:
            # GTK's main loop is up now, so the indicator can attach to it.
            tray_holder["icon"] = start_tray(on_open=show_window, on_quit=quit_app)

    window.events.shown += on_shown
    if not TRAY_NEEDS_RUNNING_LOOP:
        tray_holder["icon"] = start_tray(on_open=show_window, on_quit=quit_app)
    webview.start(debug=bool(config.config.debug))
