from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from sharebox.app.db import Database, TrustedDevice, hash_token, new_token


def _slug_base(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .") or "Device"
    return cleaned[:80]


class PairingService:
    def __init__(self, db: Database, ttl_seconds: int = 300) -> None:
        self.db = db
        self.ttl_seconds = ttl_seconds
        self._active_pairing_id: str | None = None

    def start_pairing(self) -> dict:
        pairing_id = str(uuid.uuid4())
        token = new_token(24)
        expires = datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)
        expires_at = expires.replace(microsecond=0).isoformat()
        session = self.db.create_pairing(pairing_id, token, expires_at)
        self._active_pairing_id = pairing_id
        return {
            "pairing_id": session.pairing_id,
            "token": session.token,
            "expires_at": session.expires_at,
            "ttl_seconds": self.ttl_seconds,
        }

    def cancel_pairing(self) -> None:
        self._active_pairing_id = None
        for req in self.db.list_pending_pairing_requests():
            self.db.decline_pairing_request(req["request_id"])

    def _validate_session(self, token: str):
        session = self.db.get_pairing_by_token(token)
        if not session:
            raise ValueError("INVALID_PAIRING")
        if session.consumed_at:
            raise ValueError("PAIRING_CONSUMED")
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(session.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if now > expires:
            raise ValueError("PAIRING_EXPIRED")
        return session

    def request_pairing(self, token: str, suggested_name: str | None = None) -> dict:
        """Device asks to pair; host must approve and choose the final name."""
        session = self._validate_session(token)
        request_id = str(uuid.uuid4())
        claim_secret = new_token(24)
        name = (suggested_name or "").strip() or None
        try:
            req = self.db.create_pairing_request(
                request_id,
                session.pairing_id,
                name,
                hash_token(claim_secret),
            )
        except ValueError as exc:
            if str(exc) == "PAIRING_BUSY":
                raise
            raise
        return {
            **req,
            "claim_secret": claim_secret,
        }

    def approve_request(self, request_id: str, display_name: str) -> tuple[TrustedDevice, str, dict]:
        req = self.db.get_pairing_request(request_id)
        if not req or req["status"] != "pending":
            raise ValueError("INVALID_REQUEST")
        session = self.db.get_pairing_by_id(req["pairing_id"])
        if not session:
            raise ValueError("INVALID_PAIRING")
        if session.consumed_at:
            raise ValueError("PAIRING_CONSUMED")
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(session.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if now > expires:
            raise ValueError("PAIRING_EXPIRED")

        name = display_name.strip() or (req.get("suggested_name") or "Trusted device")
        device_id = str(uuid.uuid4())
        device_token = new_token(32)
        folder_slug = self._unique_slug(name)
        device = self.db.create_device(
            device_id=device_id,
            display_name=name,
            folder_slug=folder_slug,
            token_hash=hash_token(device_token),
        )
        updated = self.db.approve_pairing_request(
            request_id, name, device_id, device_token, folder_slug
        )
        self.db.consume_pairing(session.pairing_id)
        self._active_pairing_id = None
        assert updated
        return device, device_token, updated

    def decline_request(self, request_id: str) -> dict:
        req = self.db.get_pairing_request(request_id)
        if not req or req["status"] != "pending":
            raise ValueError("INVALID_REQUEST")
        updated = self.db.decline_pairing_request(request_id)
        assert updated
        return updated

    def request_status(self, request_id: str, claim_secret: str | None = None) -> dict:
        req = self.db.get_pairing_request(request_id)
        if not req:
            raise ValueError("INVALID_REQUEST")
        if req["status"] == "approved":
            if not claim_secret:
                return {
                    "status": "approved",
                    "request_id": request_id,
                    "display_name": req.get("display_name"),
                }
            claimed = self.db.claim_pairing_token(request_id, claim_secret)
            if not claimed:
                raise ValueError("INVALID_REQUEST")
            if claimed.get("status") == "forbidden":
                raise ValueError("FORBIDDEN")
            if claimed.get("device_token"):
                return {
                    "status": "approved",
                    "request_id": request_id,
                    "device_id": claimed["device_id"],
                    "display_name": claimed["display_name"],
                    "folder_slug": claimed["folder_slug"],
                    "device_token": claimed["device_token"],
                }
            return {
                "status": "approved",
                "request_id": request_id,
                "display_name": claimed.get("display_name"),
            }
        return {
            "status": req["status"],
            "request_id": request_id,
            "suggested_name": req.get("suggested_name"),
            "display_name": req.get("display_name"),
        }

    def _unique_slug(self, display_name: str) -> str:
        base = _slug_base(display_name)
        existing = {d.folder_slug for d in self.db.list_devices(include_revoked=True)}
        if base not in existing:
            return base
        n = 2
        while f"{base} ({n})" in existing:
            n += 1
        return f"{base} ({n})"


class AuthService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def authenticate(self, token: str | None) -> TrustedDevice | None:
        if not token:
            return None
        device = self.db.find_device_by_token(token)
        if device:
            self.db.touch_device(device.device_id)
        return device
