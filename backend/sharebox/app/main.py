from __future__ import annotations

import asyncio
import logging
import os
import socket
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
from sharebox.app.state import RuntimeState, ServiceState
from sharebox.app.watcher import FolderWatcher

logger = logging.getLogger("sharebox")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


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
        try:
            config.shared_folder_path()
            if os.environ.get("SHAREBOX_DISABLE_WATCHER") != "1":
                watcher.watch(fs.root)
            addrs: list[bytes] = []
            for a in runtime.lan_addresses:
                try:
                    addrs.append(socket.inet_aton(a))
                except OSError:
                    pass
            if os.environ.get("SHAREBOX_DISABLE_MDNS") != "1":
                advertiser.start(addrs)
            runtime.state = ServiceState.SHARING
            runtime.sharing = True
            runtime.error = None
            logger.info("ShareBox ready on port %s — folder %s", runtime.port, fs.root)
            yield
        finally:
            runtime.state = ServiceState.STOPPING
            watcher.stop()
            advertiser.stop()
            runtime.sharing = False
            runtime.state = ServiceState.NOT_RUNNING

    app = FastAPI(title="ShareBox", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

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
        if full_path.startswith(("api/", "assets/")):
            return JSONResponse(
                {"error": {"code": "NOT_FOUND", "message": "Not found"}},
                status_code=404,
            )
        # Prefer real static files when present (e.g. favicon).
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
