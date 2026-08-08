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
    return datetime.now(timezone.utc).isoformat()


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

                CREATE TABLE IF NOT EXISTS clipboard_items (
                    item_id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    source_label TEXT NOT NULL,
                    device_id TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transfers (
                    transfer_id TEXT PRIMARY KEY,
                    direction TEXT NOT NULL,
                    device_id TEXT,
                    device_label TEXT NOT NULL,
                    path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    size INTEGER,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_transfers_created
                    ON transfers(created_at DESC);

                CREATE TABLE IF NOT EXISTS pairing_requests (
                    request_id TEXT PRIMARY KEY,
                    pairing_id TEXT NOT NULL,
                    suggested_name TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    display_name TEXT,
                    device_id TEXT,
                    device_token TEXT,
                    folder_slug TEXT,
                    claim_secret_hash TEXT
                );
                """
            )
            # Migrations for DBs created before claim_secret_hash existed.
            cols = {
                r[1]
                for r in conn.execute("PRAGMA table_info(pairing_requests)").fetchall()
            }
            if "claim_secret_hash" not in cols:
                conn.execute(
                    "ALTER TABLE pairing_requests ADD COLUMN claim_secret_hash TEXT"
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

    def get_pairing_by_id(self, pairing_id: str) -> PairingSession | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM pairing_sessions WHERE pairing_id = ?",
                (pairing_id,),
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

    def add_clipboard_item(
        self,
        item_id: str,
        text: str,
        source_label: str,
        device_id: str | None,
        *,
        max_items: int = 20,
    ) -> dict:
        created = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO clipboard_items(item_id, text, source_label, device_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_id, text, source_label, device_id, created),
            )
            # FIFO: keep newest max_items; drop oldest from the bottom.
            conn.execute(
                """
                DELETE FROM clipboard_items WHERE item_id NOT IN (
                    SELECT item_id FROM (
                        SELECT item_id FROM clipboard_items
                        ORDER BY created_at DESC, rowid DESC
                        LIMIT ?
                    )
                )
                """,
                (max_items,),
            )
        return {
            "item_id": item_id,
            "text": text,
            "source_label": source_label,
            "device_id": device_id,
            "created_at": created,
        }

    def list_clipboard(self, limit: int = 20) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT item_id, text, source_label, device_id, created_at
                FROM clipboard_items
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "item_id": r["item_id"],
                "text": r["text"],
                "source_label": r["source_label"],
                "device_id": r["device_id"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def delete_clipboard_item(self, item_id: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute(
                "DELETE FROM clipboard_items WHERE item_id = ?",
                (item_id,),
            )
            return cur.rowcount > 0

    def record_transfer(
        self,
        transfer_id: str,
        direction: str,
        device_id: str | None,
        device_label: str,
        path: str,
        name: str,
        size: int | None,
        *,
        max_items: int = 500,
    ) -> dict:
        created = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO transfers(
                    transfer_id, direction, device_id, device_label,
                    path, name, size, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (transfer_id, direction, device_id, device_label, path, name, size, created),
            )
            # Rolling window; this is an activity log, not an audit trail.
            conn.execute(
                """
                DELETE FROM transfers WHERE transfer_id NOT IN (
                    SELECT transfer_id FROM (
                        SELECT transfer_id FROM transfers
                        ORDER BY created_at DESC, rowid DESC
                        LIMIT ?
                    )
                )
                """,
                (max_items,),
            )
        return {
            "transfer_id": transfer_id,
            "direction": direction,
            "device_id": device_id,
            "device_label": device_label,
            "path": path,
            "name": name,
            "size": size,
            "created_at": created,
        }

    def list_transfers(self, limit: int = 100, device_id: str | None = None) -> list[dict]:
        query = """
            SELECT transfer_id, direction, device_id, device_label, path, name, size, created_at
            FROM transfers
        """
        params: list = []
        if device_id is not None:
            query += " WHERE device_id = ?"
            params.append(device_id)
        query += " ORDER BY created_at DESC, rowid DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def clear_transfers(self) -> int:
        with self.connect() as conn:
            return conn.execute("DELETE FROM transfers").rowcount

    def create_pairing_request(
        self,
        request_id: str,
        pairing_id: str,
        suggested_name: str | None,
        claim_secret_hash: str,
    ) -> dict:
        created = utc_now()
        with self.connect() as conn:
            existing = conn.execute(
                """
                SELECT request_id FROM pairing_requests
                WHERE pairing_id = ? AND status = 'pending'
                """,
                (pairing_id,),
            ).fetchone()
            if existing:
                raise ValueError("PAIRING_BUSY")
            conn.execute(
                """
                INSERT INTO pairing_requests(
                    request_id, pairing_id, suggested_name, status, created_at, claim_secret_hash
                ) VALUES (?, ?, ?, 'pending', ?, ?)
                """,
                (request_id, pairing_id, suggested_name, created, claim_secret_hash),
            )
        return self.get_pairing_request(request_id)  # type: ignore[return-value]

    def get_pairing_request(self, request_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM pairing_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if not row:
            return None
        return dict(row)

    def list_pending_pairing_requests(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM pairing_requests
                WHERE status = 'pending'
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def approve_pairing_request(
        self,
        request_id: str,
        display_name: str,
        device_id: str,
        device_token: str,
        folder_slug: str,
    ) -> dict | None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE pairing_requests
                SET status = 'approved',
                    resolved_at = ?,
                    display_name = ?,
                    device_id = ?,
                    device_token = ?,
                    folder_slug = ?
                WHERE request_id = ? AND status = 'pending'
                """,
                (utc_now(), display_name, device_id, device_token, folder_slug, request_id),
            )
        return self.get_pairing_request(request_id)

    def decline_pairing_request(self, request_id: str) -> dict | None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE pairing_requests
                SET status = 'declined', resolved_at = ?
                WHERE request_id = ? AND status = 'pending'
                """,
                (utc_now(), request_id),
            )
        return self.get_pairing_request(request_id)

    def claim_pairing_token(self, request_id: str, claim_secret: str) -> dict | None:
        """Atomically return approved credentials once when claim_secret matches."""
        secret_hash = hash_token(claim_secret)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM pairing_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if not row:
                return None
            if row["status"] != "approved":
                return dict(row)
            if not row["device_token"]:
                return dict(row)  # already claimed
            if row["claim_secret_hash"] != secret_hash:
                return {"status": "forbidden"}
            payload = dict(row)
            cur = conn.execute(
                """
                UPDATE pairing_requests
                SET device_token = NULL
                WHERE request_id = ? AND device_token IS NOT NULL AND claim_secret_hash = ?
                """,
                (request_id, secret_hash),
            )
            if cur.rowcount == 0:
                return dict(
                    conn.execute(
                        "SELECT * FROM pairing_requests WHERE request_id = ?",
                        (request_id,),
                    ).fetchone()
                )
            return payload

