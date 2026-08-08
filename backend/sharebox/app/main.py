from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from sharebox.app.api import AppContext, router, set_context
from sharebox.app.auth import AuthService, PairingService
from sharebox.app.config import ConfigStore
from sharebox.app.db import Database
from sharebox.app.discovery import MdnsAdvertiser
from sharebox.app.errors import AppError, app_error_handler
from sharebox.app.events import bus
from sharebox.app.files import FilesystemService
from sharebox.app.network import list_lan_addresses
from sharebox.app.security import is_loopback
from sharebox.app.state import RuntimeState, ServiceState
from sharebox.app.tls import CertificateStore
from sharebox.app.watcher import FolderWatcher

logger = logging.getLogger("sharebox")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
HOST_UI_DIR = Path(__file__).resolve().parent.parent / "host"
# Repo checkout: desktop UI lives beside backend/
REPO_HOST_UI = Path(__file__).resolve().parents[3] / "desktop" / "sharebox_desktop"


def _configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def create_app(app_data_dir: Path | None = None) -> FastAPI:
    config = ConfigStore(app_data_dir)
    _configure_logging(config.config.debug or os.environ.get("SHAREBOX_DEBUG") == "1")

    db = Database(config.db_path)
    fs = FilesystemService(config.shared_folder_path())
    auth = AuthService(db)
    pairing = PairingService(db, ttl_seconds=config.config.pairing_ttl_seconds)
    runtime = RuntimeState(port=config.config.port)
    ctx = AppContext(config, db, fs, auth, pairing, runtime)
    set_context(ctx)

    certs = CertificateStore(config.app_data_dir)
    advertiser = MdnsAdvertiser(config.config.port, config.config.host_name)
    loop_holder: dict[str, asyncio.AbstractEventLoop] = {}

    def on_fs_change(_event_type: str) -> None:
        loop = loop_holder.get("loop")
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(
                bus.publish({"type": "fs_changed", "reason": "watch"}),
                loop,
            )

    watcher = FolderWatcher(on_fs_change)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        loop_holder["loop"] = asyncio.get_running_loop()
        runtime.state = ServiceState.INITIALIZING
        runtime.lan_addresses = list_lan_addresses()
        runtime.port = config.config.port
        runtime.use_https = config.config.use_https
        if runtime.use_https:
            certs.ensure(runtime.lan_addresses, config.config.host_name)
            runtime.cert_fingerprint = certs.fingerprint()
        try:
            config.shared_folder_path()
            if os.environ.get("SHAREBOX_DISABLE_WATCHER") != "1":
                watcher.watch(fs.root)
            # mDNS / sharebox.local disabled for now — mobile browsers were unreliable.
            # Opt in later with SHAREBOX_ENABLE_MDNS=1 when we ship a friendly name again.
            if os.environ.get("SHAREBOX_ENABLE_MDNS") == "1":
                advertiser.start(runtime.lan_addresses)
                runtime.mdns_active = advertiser.active
                runtime.mdns_ip = advertiser.advertised_ip
            runtime.state = ServiceState.SHARING
            runtime.sharing = True
            runtime.error = None
            logger.info("ShareBox ready on port %s — folder %s", runtime.port, fs.root)
            yield
        finally:
            runtime.state = ServiceState.STOPPING
            watcher.stop()
            advertiser.stop()
            runtime.mdns_active = False
            runtime.mdns_ip = None
            runtime.sharing = False
            runtime.state = ServiceState.NOT_RUNNING

    app = FastAPI(title="ShareBox", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(AppError, app_error_handler)
    # Control Center is same-origin (/host). CORS covers Vite dev + loopback API origins
    # in case WebView still sends a preflight.
    port = config.config.port
    control_port = config.effective_control_port()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://127.0.0.1:{port}",
            f"http://localhost:{port}",
            f"https://127.0.0.1:{port}",
            f"https://localhost:{port}",
            # Control Center window when HTTPS moves the LAN listener off plain HTTP.
            f"http://127.0.0.1:{control_port}",
            f"http://localhost:{control_port}",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-ShareBox-Token"],
    )
    app.include_router(router)

    host_ui = HOST_UI_DIR if (HOST_UI_DIR / "control_center.html").exists() else REPO_HOST_UI
    if (host_ui / "control_center.html").exists():

        @app.middleware("http")
        async def restrict_host_ui(request, call_next):
            if request.url.path.startswith("/host"):
                if not is_loopback(request):
                    return JSONResponse(
                        {"error": {"code": "FORBIDDEN", "message": "Control Center is local-only"}},
                        status_code=403,
                    )
            return await call_next(request)

        app.mount("/host", StaticFiles(directory=host_ui, html=True), name="host_ui")

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index = STATIC_DIR / "index.html"

    @app.get("/")
    async def spa_root():
        if index.exists():
            return FileResponse(index)
        return JSONResponse(
            {
                "name": "ShareBox",
                "message": "Web client not built yet. Run npm run build in /web.",
                "api": "/api/v1/health",
            }
        )

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith(("api/", "assets/", "host/")):
            return JSONResponse(
                {"error": {"code": "NOT_FOUND", "message": "Not found"}},
                status_code=404,
            )
        candidate = STATIC_DIR / full_path
        if candidate.is_file() and STATIC_DIR in candidate.resolve().parents:
            return FileResponse(candidate)
        if index.exists():
            return FileResponse(index)
        return JSONResponse(
            {"error": {"code": "NOT_FOUND", "message": "Not found"}},
            status_code=404,
        )

    app.state.sharebox_ctx = ctx  # type: ignore[attr-defined]
    app.state.watcher = watcher  # type: ignore[attr-defined]
    app.state.advertiser = advertiser  # type: ignore[attr-defined]
    app.state.certificates = certs  # type: ignore[attr-defined]
    return app


app = create_app()


def run() -> None:
    import uvicorn

    cfg = ConfigStore()
    uvicorn.run(
        "sharebox.app.main:app",
        host=cfg.config.bind_host,
        port=cfg.config.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
