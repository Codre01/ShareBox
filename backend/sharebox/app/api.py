from __future__ import annotations

import asyncio
import io
import logging
import mimetypes
import uuid
from pathlib import Path
from typing import Annotated, Any

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
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
from sharebox.app.security import (
    MAX_CLIPBOARD_CHARS,
    MAX_CLIPBOARD_ITEMS,
    MAX_TRANSFER_HISTORY,
    MAX_UPLOAD_FILE_BYTES,
    MAX_UPLOAD_REQUEST_BYTES,
    is_loopback,
    require_loopback,
)
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


async def record_transfer(
    direction: str,
    device: TrustedDevice | None,
    path: str,
    name: str,
    size: int | None,
) -> dict:
    """Log a transfer and tell listening clients about it.

    Downloads are recorded when the response is handed to the client, so this
    means "started", not "finished on the far end" — we never learn that.
    """
    ctx = get_ctx()
    entry = ctx.db.record_transfer(
        transfer_id=str(uuid.uuid4()),
        direction=direction,
        device_id=device.device_id if device else None,
        device_label=device.display_name if device else ctx.config.config.host_name,
        path=path,
        name=name,
        size=size,
        max_items=MAX_TRANSFER_HISTORY,
    )
    await bus.publish({"type": "transfer", "direction": direction})
    return entry


class PairCompleteBody(BaseModel):
    token: str
    display_name: str | None = None


class PairRequestBody(BaseModel):
    token: str
    suggested_name: str | None = None


class PairApproveBody(BaseModel):
    request_id: str
    display_name: str = Field(min_length=1, max_length=80)


class PairDeclineBody(BaseModel):
    request_id: str


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
async def status(
    request: Request,
    device: TrustedDevice | None = Depends(optional_device),
) -> dict[str, Any]:
    ctx = get_ctx()
    cfg = ctx.config.config
    data = ctx.runtime.as_dict()
    data.update(
        {
            "host_name": cfg.host_name,
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
    # Host-only details — never expose pairing secrets or folder paths on the LAN.
    if is_loopback(request):
        data["shared_folder"] = cfg.shared_folder
    else:
        data.pop("active_pairing", None)
        data.pop("shared_folder", None)
    return data


@router.post("/sharing/start")
async def start_sharing(request: Request) -> dict[str, Any]:
    require_loopback(request)
    ctx = get_ctx()
    ctx.runtime.sharing = True
    ctx.runtime.state = ServiceState.SHARING
    ctx.runtime.error = None
    ctx.runtime.lan_addresses = list_lan_addresses()
    ctx.runtime.port = ctx.config.config.port
    return ctx.runtime.as_dict()


@router.post("/sharing/stop")
async def stop_sharing(request: Request) -> dict[str, Any]:
    require_loopback(request)
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
    await record_transfer(
        "download", device, ctx.fs.relative_path(target), target.name, target.stat().st_size
    )
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
    dest_dir = ctx.fs.ensure_device_folder(device.folder_slug)
    saved: list[dict[str, Any]] = []
    total_written = 0
    for upload in files:
        original = upload.filename or "upload.bin"
        final_path = ctx.fs.unique_name(dest_dir, original)
        tmp_path = final_path.with_name(final_path.name + ".sharebox.tmp")
        written = 0
        try:
            async with aiofiles.open(tmp_path, "wb") as out:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    total_written += len(chunk)
                    if written > MAX_UPLOAD_FILE_BYTES:
                        raise_http(
                            "FILE_TOO_LARGE",
                            f"File exceeds {MAX_UPLOAD_FILE_BYTES // (1024 * 1024)} MiB limit",
                            413,
                        )
                    if total_written > MAX_UPLOAD_REQUEST_BYTES:
                        raise_http(
                            "UPLOAD_TOO_LARGE",
                            "Upload request exceeds size limit",
                            413,
                        )
                    await out.write(chunk)
            tmp_path.replace(final_path)
            saved.append(
                {
                    "name": final_path.name,
                    "path": ctx.fs.relative_path(final_path),
                    "size": final_path.stat().st_size,
                }
            )
            await record_transfer(
                "upload",
                device,
                ctx.fs.relative_path(final_path),
                final_path.name,
                final_path.stat().st_size,
            )
        except HTTPException:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
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
async def pairing_start(request: Request) -> dict[str, Any]:
    require_loopback(request)
    ctx = get_ctx()
    session = ctx.pairing.start_pairing()
    port = ctx.config.config.port
    lan_ip = primary_lan_address() or "127.0.0.1"
    # LAN IP only for now (QR + copy link). Friendly hostnames can return later.
    pair_url = f"http://{lan_ip}:{port}/?pair={session['token']}"
    session["pair_url"] = pair_url
    session["pair_url_ip"] = pair_url
    session["lan_addresses"] = list_lan_addresses()
    session["port"] = port
    session["mdns_active"] = False
    ctx.runtime.active_pairing = session
    return session


@router.post("/pairing/cancel")
async def pairing_cancel(request: Request) -> dict[str, str]:
    require_loopback(request)
    ctx = get_ctx()
    ctx.pairing.cancel_pairing()
    ctx.runtime.active_pairing = None
    return {"status": "cancelled"}


@router.post("/pairing/request")
async def pairing_request(body: PairRequestBody) -> dict[str, Any]:
    """Device initiates pairing; waits for host to name + approve."""
    ctx = get_ctx()
    try:
        req = ctx.pairing.request_pairing(body.token, body.suggested_name)
    except ValueError as exc:
        code = str(exc)
        messages = {
            "INVALID_PAIRING": ("Invalid pairing code", 400),
            "PAIRING_CONSUMED": ("Pairing code already used", 410),
            "PAIRING_EXPIRED": ("Pairing code expired", 410),
            "PAIRING_BUSY": ("Another device is already waiting to pair", 409),
        }
        msg, status = messages.get(code, ("Pairing failed", 400))
        raise_http(code, msg, status)
    await bus.publish({"type": "pairing_request", "request_id": req["request_id"]})
    return {
        "request_id": req["request_id"],
        "status": req["status"],
        "suggested_name": req.get("suggested_name"),
        "claim_secret": req["claim_secret"],
    }


@router.get("/pairing/request/{request_id}")
async def pairing_request_status(
    request_id: str,
    claim_secret: str | None = Query(default=None),
) -> dict[str, Any]:
    ctx = get_ctx()
    try:
        return ctx.pairing.request_status(request_id, claim_secret)
    except ValueError as exc:
        if str(exc) == "FORBIDDEN":
            raise_http("FORBIDDEN", "Invalid claim secret", 403)
        raise_http("INVALID_REQUEST", "Pairing request not found", 404)


@router.get("/pairing/pending")
async def pairing_pending(request: Request) -> dict[str, Any]:
    require_loopback(request)
    ctx = get_ctx()
    return {"requests": ctx.db.list_pending_pairing_requests()}


@router.post("/pairing/approve")
async def pairing_approve(request: Request, body: PairApproveBody) -> dict[str, Any]:
    require_loopback(request)
    ctx = get_ctx()
    try:
        device, _token, _req = ctx.pairing.approve_request(body.request_id, body.display_name)
    except ValueError as exc:
        code = str(exc)
        messages = {
            "INVALID_REQUEST": ("Pairing request not found", 404),
            "INVALID_PAIRING": ("Invalid pairing session", 400),
            "PAIRING_CONSUMED": ("Pairing already completed", 410),
            "PAIRING_EXPIRED": ("Pairing code expired", 410),
        }
        msg, status = messages.get(code, ("Approve failed", 400))
        raise_http(code, msg, status)
    ctx.runtime.active_pairing = None
    await bus.publish({"type": "pairing_approved", "request_id": body.request_id})
    return {
        "device_id": device.device_id,
        "display_name": device.display_name,
        "folder_slug": device.folder_slug,
    }


@router.post("/pairing/decline")
async def pairing_decline(request: Request, body: PairDeclineBody) -> dict[str, Any]:
    require_loopback(request)
    ctx = get_ctx()
    try:
        req = ctx.pairing.decline_request(body.request_id)
    except ValueError:
        raise_http("INVALID_REQUEST", "Pairing request not found", 404)
    await bus.publish({"type": "pairing_declined", "request_id": body.request_id})
    return {"status": req["status"], "request_id": req["request_id"]}


@router.get("/devices")
async def list_devices(request: Request) -> dict[str, Any]:
    require_loopback(request)
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
async def rename_device(
    request: Request, device_id: str, body: RenameDeviceBody
) -> dict[str, Any]:
    require_loopback(request)
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
async def revoke_device(request: Request, device_id: str) -> dict[str, str]:
    require_loopback(request)
    ctx = get_ctx()
    device = ctx.db.get_device(device_id)
    if not device or device.revoked_at:
        raise_http("NOT_FOUND", "Device not found", 404)
    ctx.db.revoke_device(device_id)
    return {"status": "revoked"}


class ClipboardBody(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_CLIPBOARD_CHARS)


async def require_device_or_host(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_sharebox_token: Annotated[str | None, Header(alias="X-ShareBox-Token")] = None,
) -> TrustedDevice | None:
    """Trusted device, or the host Control Center on loopback (returns None for host)."""
    ctx = get_ctx()
    token = extract_bearer(authorization, x_sharebox_token)
    device = ctx.auth.authenticate(token)
    if device:
        return device
    if is_loopback(request):
        return None
    raise_http("UNAUTHORIZED", "Authentication required", 401)
    return None  # pragma: no cover


@router.get("/clipboard")
async def list_clipboard(
    request: Request,
    actor: TrustedDevice | None = Depends(require_device_or_host),
) -> dict[str, Any]:
    ctx = get_ctx()
    return {"items": ctx.db.list_clipboard()}


@router.post("/clipboard")
async def post_clipboard(
    body: ClipboardBody,
    request: Request,
    actor: TrustedDevice | None = Depends(require_device_or_host),
) -> dict[str, Any]:
    import uuid

    ctx = get_ctx()
    text = body.text.strip("\x00")
    if not text.strip():
        raise_http("EMPTY_CLIPBOARD", "Clipboard text is empty", 400)
    if len(text) > MAX_CLIPBOARD_CHARS:
        raise_http("CLIPBOARD_TOO_LARGE", "Clipboard text is too large", 413)
    if actor is None:
        source_label = ctx.config.config.host_name or "This computer"
        device_id = None
    else:
        source_label = actor.display_name
        device_id = actor.device_id
    item = ctx.db.add_clipboard_item(
        item_id=str(uuid.uuid4()),
        text=text,
        source_label=source_label,
        device_id=device_id,
        max_items=MAX_CLIPBOARD_ITEMS,
    )
    await bus.publish({"type": "clipboard_changed", "item_id": item["item_id"]})
    return {"item": item}


@router.delete("/clipboard/{item_id}")
async def delete_clipboard(
    item_id: str,
    request: Request,
    actor: TrustedDevice | None = Depends(require_device_or_host),
) -> dict[str, str]:
    ctx = get_ctx()
    if not ctx.db.delete_clipboard_item(item_id):
        raise_http("NOT_FOUND", "Clipboard item not found", 404)
    await bus.publish({"type": "clipboard_changed", "item_id": item_id})
    return {"status": "deleted"}


@router.get("/transfers")
async def list_transfers(
    request: Request,
    limit: int = Query(default=100, ge=1, le=MAX_TRANSFER_HISTORY),
    actor: TrustedDevice | None = Depends(require_device_or_host),
) -> dict[str, Any]:
    """History of what moved. The host sees every device; a device sees itself."""
    ctx = get_ctx()
    if actor is None:
        return {"items": ctx.db.list_transfers(limit), "scope": "all"}
    return {
        "items": ctx.db.list_transfers(limit, device_id=actor.device_id),
        "scope": "device",
    }


@router.delete("/transfers")
async def clear_transfers(request: Request) -> dict[str, Any]:
    require_loopback(request)
    ctx = get_ctx()
    removed = ctx.db.clear_transfers()
    await bus.publish({"type": "transfer", "direction": "cleared"})
    return {"status": "cleared", "removed": removed}


@router.get("/settings")
async def get_settings(request: Request) -> dict[str, Any]:
    require_loopback(request)
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
async def update_settings(request: Request, body: SettingsUpdateBody) -> dict[str, Any]:
    require_loopback(request)
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
    return await get_settings(request)


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
async def qr_png(request: Request) -> StreamingResponse:
    """Render current pairing URL as a QR PNG for the Control Center."""
    require_loopback(request)
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
