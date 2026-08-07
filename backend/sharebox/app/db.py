from __future__ import annotations

import hashlib
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


@dataclass
class TrustedDevice:
    device_id: str
    display_name: str
    folder_slug: str
    token_hash: str
    created_at: str
    last_seen_at: str | None
    revoked_at: str | None = None


@dataclass
class PairingSession:
    pairing_id: str
    token: str
    created_at: str
    expires_at: str
    consumed_at: str | None = None


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS trusted_devices (
                    device_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    folder_slug TEXT NOT NULL UNIQUE,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT,
                    revoked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS pairing_sessions (
                    pairing_id TEXT PRIMARY KEY,
                    token TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY(device_id) REFERENCES trusted_devices(device_id)
                );

                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def create_pairing(self, pairing_id: str, token: str, expires_at: str) -> PairingSession:
        created = utc_now()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO pairing_sessions(pairing_id, token, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (pairing_id, token, created, expires_at),
            )
        return PairingSession(pairing_id, token, created, expires_at)

    def get_pairing_by_token(self, token: str) -> PairingSession | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM pairing_sessions WHERE token = ?",
                (token,),
            ).fetchone()
        if not row:
            return None
        return PairingSession(
            row["pairing_id"],
            row["token"],
            row["created_at"],
            row["expires_at"],
            row["consumed_at"],
        )

    def consume_pairing(self, pairing_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE pairing_sessions SET consumed_at = ? WHERE pairing_id = ?",
                (utc_now(), pairing_id),
            )

    def create_device(
        self,
        device_id: str,
        display_name: str,
        folder_slug: str,
        token_hash: str,
    ) -> TrustedDevice:
        created = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO trusted_devices(
                    device_id, display_name, folder_slug, token_hash, created_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (device_id, display_name, folder_slug, token_hash, created, created),
            )
        return TrustedDevice(device_id, display_name, folder_slug, token_hash, created, created)

    def list_devices(self, include_revoked: bool = False) -> list[TrustedDevice]:
        query = "SELECT * FROM trusted_devices"
        if not include_revoked:
            query += " WHERE revoked_at IS NULL"
        query += " ORDER BY created_at DESC"
        with self.connect() as conn:
            rows = conn.execute(query).fetchall()
        return [self._device_from_row(r) for r in rows]

    def get_device(self, device_id: str) -> TrustedDevice | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM trusted_devices WHERE device_id = ?",
                (device_id,),
            ).fetchone()
        return self._device_from_row(row) if row else None

    def find_device_by_token(self, token: str) -> TrustedDevice | None:
        th = hash_token(token)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM trusted_devices WHERE token_hash = ? AND revoked_at IS NULL",
                (th,),
            ).fetchone()
        return self._device_from_row(row) if row else None

    def touch_device(self, device_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE trusted_devices SET last_seen_at = ? WHERE device_id = ?",
                (utc_now(), device_id),
            )

    def rename_device(self, device_id: str, display_name: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE trusted_devices SET display_name = ? WHERE device_id = ?",
                (display_name, device_id),
            )

    def revoke_device(self, device_id: str) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                "UPDATE trusted_devices SET revoked_at = ? WHERE device_id = ?",
                (now, device_id),
            )
            conn.execute(
                "UPDATE sessions SET revoked_at = ? WHERE device_id = ? AND revoked_at IS NULL",
                (now, device_id),
            )

    def create_session(self, session_id: str, device_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sessions(session_id, device_id, created_at) VALUES (?, ?, ?)",
                (session_id, device_id, utc_now()),
            )

    def is_session_valid(self, session_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT s.session_id FROM sessions s
                JOIN trusted_devices d ON d.device_id = s.device_id
                WHERE s.session_id = ? AND s.revoked_at IS NULL AND d.revoked_at IS NULL
                """,
                (session_id,),
            ).fetchone()
        return row is not None

    @staticmethod
    def _device_from_row(row: sqlite3.Row) -> TrustedDevice:
        return TrustedDevice(
            device_id=row["device_id"],
            display_name=row["display_name"],
            folder_slug=row["folder_slug"],
            token_hash=row["token_hash"],
            created_at=row["created_at"],
            last_seen_at=row["last_seen_at"],
            revoked_at=row["revoked_at"],
        )
