from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from sharebox.app.db import Database, TrustedDevice, hash_token, new_token, utc_now


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

    def complete_pairing(self, token: str, display_name: str | None = None) -> tuple[TrustedDevice, str]:
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

        name = (display_name or "Trusted device").strip() or "Trusted device"
        device_id = str(uuid.uuid4())
        device_token = new_token(32)
        folder_slug = self._unique_slug(name)
        device = self.db.create_device(
            device_id=device_id,
            display_name=name,
            folder_slug=folder_slug,
            token_hash=hash_token(device_token),
        )
        self.db.consume_pairing(session.pairing_id)
        self._active_pairing_id = None
        return device, device_token

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
