from __future__ import annotations

import asyncio
import io
import logging
import mimetypes
from pathlib import Path
from typing import Annotated, Any

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from sharebox.app.auth import AuthService, PairingService
from sharebox.app.config import ConfigStore
from sharebox.app.db import Database, TrustedDevice
from sharebox.app.errors import raise_http
from sharebox.app.events import bus
from sharebox.app.files import FilesystemService, PathEscapeError
from sharebox.app.network import list_lan_addresses, primary_lan_address
from sharebox.app.state import RuntimeState, ServiceState

logger = logging.getLogger("sharebox.api")

router = APIRouter(prefix="/api/v1")


class AppContext:
    def __init__(
        self,
        config: ConfigStore,
        db: Database,
        fs: FilesystemService,
        auth: AuthService,
        pairing: PairingService,
        runtime: RuntimeState,
    ) -> None:
        self.config = config
        self.db = db
        self.fs = fs
        self.auth = auth
        self.pairing = pairing
        self.runtime = runtime


_ctx: AppContext | None = None


def set_context(ctx: AppContext) -> None:
    global _ctx
    _ctx = ctx


def get_ctx() -> AppContext:
    if _ctx is None:
        raise RuntimeError("App context not initialized")
    return _ctx


def extract_bearer(authorization: str | None, x_sharebox_token: str | None) -> str | None:
    if x_sharebox_token:
        return x_sharebox_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


async def require_device(
    authorization: Annotated[str | None, Header()] = None,
    x_sharebox_token: Annotated[str | None, Header(alias="X-ShareBox-Token")] = None,
) -> TrustedDevice:
    ctx = get_ctx()
    token = extract_bearer(authorization, x_sharebox_token)
    device = ctx.auth.authenticate(token)
    if not device:
        raise_http("UNAUTHORIZED", "Authentication required", 401)
    return device  # type: ignore[return-value]


async def optional_device(
    authorization: Annotated[str | None, Header()] = None,
    x_sharebox_token: Annotated[str | None, Header(alias="X-ShareBox-Token")] = None,
) -> TrustedDevice | None:
    ctx = get_ctx()
    token = extract_bearer(authorization, x_sharebox_token)
    return ctx.auth.authenticate(token)


class PairCompleteBody(BaseModel):
    token: str
    display_name: str | None = None


class RenameDeviceBody(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)


class SettingsUpdateBody(BaseModel):
    shared_folder: str | None = None
    host_name: str | None = None
    launch_at_startup: bool | None = None
    port: int | None = None


@router.get("/health")
async def health() -> dict[str, Any]:
    ctx = get_ctx()
    return {
        "ok": True,
        "version": "0.1.0",
        "sharing": ctx.runtime.sharing,
        "state": ctx.runtime.state.value,
    }


@router.get("/status")
async def status(device: TrustedDevice | None = Depends(optional_device)) -> dict[str, Any]:
    ctx = get_ctx()
    cfg = ctx.config.config
    data = ctx.runtime.as_dict()
    data.update(
        {
            "host_name": cfg.host_name,
            "shared_folder": cfg.shared_folder,
            "authenticated": device is not None,
            "device": None
            if not device
            else {
                "device_id": device.device_id,
                "display_name": device.display_name,
                "folder_slug": device.folder_slug,
            },
        }
    )
    return data


@router.post("/sharing/start")
async def start_sharing() -> dict[str, Any]:
    ctx = get_ctx()
    ctx.runtime.sharing = True
    ctx.runtime.state = ServiceState.SHARING
    ctx.runtime.error = None
    ctx.runtime.lan_addresses = list_lan_addresses()
    ctx.runtime.port = ctx.config.config.port
    return ctx.runtime.as_dict()


@router.post("/sharing/stop")
async def stop_sharing() -> dict[str, Any]:
    ctx = get_ctx()
    ctx.runtime.sharing = False
    ctx.runtime.state = ServiceState.READY
    ctx.runtime.active_pairing = None
    return ctx.runtime.as_dict()


@router.get("/files")
async def list_files(
    path: str = Query(default=""),
    device: TrustedDevice = Depends(require_device),
) -> dict[str, Any]:
    ctx = get_ctx()
    try:
        items = ctx.fs.list_dir(path)
    except PathEscapeError:
        raise_http("PATH_ESCAPE", "Invalid path", 400)
    except FileNotFoundError:
        raise_http("NOT_FOUND", "Folder not found", 404)
    except NotADirectoryError:
        raise_http("NOT_A_FOLDER", "Not a folder", 400)
    return {"path": path.strip("/"), "items": items}


@router.get("/files/search")
async def search_files(
    q: str = Query(min_length=1),
    device: TrustedDevice = Depends(require_device),
) -> dict[str, Any]:
    ctx = get_ctx()
    return {"query": q, "items": ctx.fs.search(q)}


@router.get("/files/download")
async def download_file(
    path: str = Query(...),
    device: TrustedDevice = Depends(require_device),
) -> FileResponse:
    ctx = get_ctx()
    try:
        target = ctx.fs.resolve(path)
    except PathEscapeError:
        raise_http("PATH_ESCAPE", "Invalid path", 400)
    if not target.exists() or not target.is_file():
        raise_http("NOT_FOUND", "File not found", 404)
    media, _ = mimetypes.guess_type(str(target))
    return FileResponse(
        path=target,
        filename=target.name,
        media_type=media or "application/octet-stream",
    )


@router.get("/files/preview")
async def preview_file(
    path: str = Query(...),
    device: TrustedDevice = Depends(require_device),
) -> FileResponse:
    """Inline preview for images and text; otherwise download metadata only via listing."""
    ctx = get_ctx()
    try:
        target = ctx.fs.resolve(path)
    except PathEscapeError:
        raise_http("PATH_ESCAPE", "Invalid path", 400)
    if not target.exists() or not target.is_file():
        raise_http("NOT_FOUND", "File not found", 404)
    media, _ = mimetypes.guess_type(str(target))
    media = media or "application/octet-stream"
    previewable = media.startswith("image/") or media.startswith("text/") or media == "application/pdf"
    if not previewable:
        raise_http("PREVIEW_UNSUPPORTED", "Preview not available for this type", 415)
    return FileResponse(path=target, media_type=media, filename=target.name)


@router.post("/files/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    device: TrustedDevice = Depends(require_device),
) -> dict[str, Any]:
    ctx = get_ctx()
    # Lazy create device folder on first upload.
    dest_dir = ctx.fs.ensure_device_folder(device.folder_slug)
    saved: list[dict[str, Any]] = []
    for upload in files:
        original = upload.filename or "upload.bin"
        final_path = ctx.fs.unique_name(dest_dir, original)
        tmp_path = final_path.with_name(final_path.name + ".sharebox.tmp")
        try:
            async with aiofiles.open(tmp_path, "wb") as out:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    await out.write(chunk)
            tmp_path.replace(final_path)
            saved.append(
                {
                    "name": final_path.name,
                    "path": ctx.fs.relative_path(final_path),
                    "size": final_path.stat().st_size,
                }
            )
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            logger.exception("Upload failed for %s", original)
            raise_http("UPLOAD_FAILED", f"Failed to upload {original}", 500)
        finally:
            await upload.close()
    await bus.publish({"type": "fs_changed", "reason": "upload"})
    return {"folder": device.folder_slug, "files": saved}


@router.post("/pairing/start")
async def pairing_start() -> dict[str, Any]:
    ctx = get_ctx()
    session = ctx.pairing.start_pairing()
    addr = primary_lan_address() or "127.0.0.1"
    port = ctx.config.config.port
    # QR payload: URL that includes pairing token for the web client.
    pair_url = f"http://{addr}:{port}/?pair={session['token']}"
    session["pair_url"] = pair_url
    session["lan_addresses"] = list_lan_addresses()
    session["port"] = port
    ctx.runtime.active_pairing = session
    return session


@router.post("/pairing/cancel")
async def pairing_cancel() -> dict[str, str]:
    ctx = get_ctx()
    ctx.pairing.cancel_pairing()
    ctx.runtime.active_pairing = None
    return {"status": "cancelled"}


@router.post("/pairing/complete")
async def pairing_complete(body: PairCompleteBody) -> dict[str, Any]:
    ctx = get_ctx()
    try:
        device, device_token = ctx.pairing.complete_pairing(body.token, body.display_name)
    except ValueError as exc:
        code = str(exc)
        messages = {
            "INVALID_PAIRING": ("Invalid pairing code", 400),
            "PAIRING_CONSUMED": ("Pairing code already used", 410),
            "PAIRING_EXPIRED": ("Pairing code expired", 410),
        }
        msg, status = messages.get(code, ("Pairing failed", 400))
        raise_http(code, msg, status)
    ctx.runtime.active_pairing = None
    return {
        "device_id": device.device_id,
        "display_name": device.display_name,
        "folder_slug": device.folder_slug,
        "device_token": device_token,
    }


@router.get("/devices")
async def list_devices() -> dict[str, Any]:
    """Host Control Center endpoint — lists trusted devices."""
    ctx = get_ctx()
    devices = [
        {
            "device_id": d.device_id,
            "display_name": d.display_name,
            "folder_slug": d.folder_slug,
            "created_at": d.created_at,
            "last_seen_at": d.last_seen_at,
        }
        for d in ctx.db.list_devices()
    ]
    return {"devices": devices}


@router.patch("/devices/{device_id}")
async def rename_device(device_id: str, body: RenameDeviceBody) -> dict[str, Any]:
    ctx = get_ctx()
    device = ctx.db.get_device(device_id)
    if not device or device.revoked_at:
        raise_http("NOT_FOUND", "Device not found", 404)
    ctx.db.rename_device(device_id, body.display_name.strip())
    updated = ctx.db.get_device(device_id)
    assert updated
    return {
        "device_id": updated.device_id,
        "display_name": updated.display_name,
        "folder_slug": updated.folder_slug,
    }


@router.delete("/devices/{device_id}")
async def revoke_device(device_id: str) -> dict[str, str]:
    ctx = get_ctx()
    device = ctx.db.get_device(device_id)
    if not device or device.revoked_at:
        raise_http("NOT_FOUND", "Device not found", 404)
    ctx.db.revoke_device(device_id)
    return {"status": "revoked"}


@router.get("/settings")
async def get_settings() -> dict[str, Any]:
    ctx = get_ctx()
    cfg = ctx.config.config
    return {
        "shared_folder": cfg.shared_folder,
        "host_name": cfg.host_name,
        "launch_at_startup": cfg.launch_at_startup,
        "port": cfg.port,
        "installation_id": cfg.installation_id,
    }


@router.patch("/settings")
async def update_settings(body: SettingsUpdateBody) -> dict[str, Any]:
    ctx = get_ctx()
    updates: dict[str, Any] = {}
    if body.shared_folder is not None:
        folder = Path(body.shared_folder)
        folder.mkdir(parents=True, exist_ok=True)
        updates["shared_folder"] = str(folder.resolve())
        ctx.fs.set_root(folder)
    if body.host_name is not None:
        updates["host_name"] = body.host_name.strip() or ctx.config.config.host_name
    if body.launch_at_startup is not None:
        updates["launch_at_startup"] = body.launch_at_startup
        try:
            from sharebox.app.startup_windows import set_launch_at_startup

            set_launch_at_startup(body.launch_at_startup)
        except Exception:
            logger.exception("Could not update launch-at-startup")
    if body.port is not None:
        if not (1024 <= body.port <= 65535):
            raise_http("INVALID_PORT", "Port must be between 1024 and 65535", 400)
        updates["port"] = body.port
        ctx.runtime.port = body.port
    if updates:
        ctx.config.update(**updates)
    return await get_settings()


@router.get("/events")
async def events(device: TrustedDevice = Depends(require_device)) -> StreamingResponse:
    async def gen():
        sub_id, queue = await bus.subscribe()
        try:
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                    import json

                    yield f"event: {event.get('type', 'message')}\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
        finally:
            await bus.unsubscribe(sub_id)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/qr.png")
async def qr_png() -> StreamingResponse:
    """Render current pairing URL as a QR PNG for the Control Center."""
    ctx = get_ctx()
    if not ctx.runtime.active_pairing:
        raise_http("NO_PAIRING", "No active pairing session", 404)
    try:
        import qrcode
    except ImportError:
        raise_http("QR_UNAVAILABLE", "QR library not installed", 500)
    url = ctx.runtime.active_pairing["pair_url"]
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
