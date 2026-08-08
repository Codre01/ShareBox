"""Streaming ZIP archives for folder and multi-file downloads."""

from __future__ import annotations

import logging
import secrets
import threading
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from sharebox.app.files import FilesystemService

logger = logging.getLogger("sharebox.archive")

READ_CHUNK = 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000
TICKET_TTL_SECONDS = 120.0


class ArchiveTooLargeError(Exception):
    """Raised when a selection expands to more files than we will archive."""


@dataclass(frozen=True)
class ArchiveEntry:
    source: Path
    arcname: str


class _StreamBuffer:
    """Sink that lets zipfile write into a generator instead of a real file.

    Deliberately has no tell()/seek(): zipfile detects the missing tell(),
    treats the stream as unseekable and emits data descriptors, which is what
    lets us stream without knowing sizes up front.
    """

    def __init__(self) -> None:
        self._parts: list[bytes] = []

    def write(self, data: bytes) -> int:
        self._parts.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        pass

    def drain(self) -> bytes:
        if not self._parts:
            return b""
        payload = b"".join(self._parts)
        self._parts.clear()
        return payload


def _within_root(fs: FilesystemService, path: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(fs.root)
    except (ValueError, OSError):
        return False
    return True


def _unique_arcname(name: str, used: set[str]) -> str:
    if name not in used:
        used.add(name)
        return name
    stem, dot, suffix = name.rpartition(".")
    base, ext = (stem, dot + suffix) if stem else (name, "")
    counter = 2
    while f"{base} ({counter}){ext}" in used:
        counter += 1
    unique = f"{base} ({counter}){ext}"
    used.add(unique)
    return unique


def collect_entries(fs: FilesystemService, paths: Sequence[str]) -> list[ArchiveEntry]:
    """Expand a selection of files/folders into the files to archive.

    Paths are resolved through FilesystemService, so traversal and symlinks
    escaping the shared folder are rejected the same way browsing is.
    """
    entries: list[ArchiveEntry] = []
    used: set[str] = set()

    for raw in paths:
        target = fs.resolve(raw)
        if not target.exists():
            raise FileNotFoundError(raw)

        # Names are relative to the item's parent, so zipping "docs" yields
        # docs/note.txt rather than a bare note.txt.
        anchor = target.parent
        sources = [target] if target.is_file() else sorted(
            child for child in target.rglob("*") if child.is_file()
        )

        for source in sources:
            relative = source.relative_to(anchor)
            # Hidden files are invisible when browsing; keep them invisible here.
            if any(part.startswith(".") for part in relative.parts):
                continue
            if not _within_root(fs, source):
                continue
            if len(entries) >= MAX_ARCHIVE_ENTRIES:
                raise ArchiveTooLargeError(
                    f"Selection exceeds {MAX_ARCHIVE_ENTRIES} files"
                )
            entries.append(ArchiveEntry(source, _unique_arcname(relative.as_posix(), used)))

    return entries


def iter_zip(entries: Iterable[ArchiveEntry]) -> Iterator[bytes]:
    """Yield a ZIP of the given entries without buffering it in memory."""
    buffer = _StreamBuffer()
    # ZIP_STORED rather than deflate: shared files are usually already-compressed
    # media, and on a LAN the link is the bottleneck, not the bytes saved.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED, allowZip64=True) as archive:
        for entry in entries:
            try:
                handle = entry.source.open("rb")
            except OSError:
                # Deleted or unreadable between listing and download.
                logger.warning("Skipping unreadable file: %s", entry.arcname)
                continue

            info = zipfile.ZipInfo(entry.arcname, _mtime(entry.source))
            info.compress_type = zipfile.ZIP_STORED
            with handle, archive.open(info, "w") as target:
                while chunk := handle.read(READ_CHUNK):
                    target.write(chunk)
                    payload = buffer.drain()
                    if payload:
                        yield payload

            payload = buffer.drain()
            if payload:
                yield payload

    yield buffer.drain()


def _mtime(path: Path) -> tuple[int, int, int, int, int, int]:
    try:
        return time.localtime(path.stat().st_mtime)[:6]  # type: ignore[return-value]
    except OSError:
        return time.localtime()[:6]  # type: ignore[return-value]


def archive_filename(fs: FilesystemService, paths: Sequence[str]) -> str:
    """A sensible .zip name for the selection."""
    if len(paths) == 1:
        name = Path(paths[0].replace("\\", "/").strip("/")).name
        if name:
            return f"{FilesystemService.sanitize_filename(name)}.zip"
    return "ShareBox files.zip"


@dataclass
class DownloadTicket:
    device_id: str
    paths: tuple[str, ...]
    filename: str
    expires_at: float


class TicketStore:
    """Short-lived single-use tickets that let the browser stream a download.

    The device token lives in localStorage and can only travel in a header,
    but a native browser download is a plain navigation with no headers.
    Buffering the archive through fetch() instead would put the whole ZIP in
    the phone's memory, which is exactly what streaming is meant to avoid.
    A ticket bridges the two: minted by an authenticated request, spent once,
    and expired within a couple of minutes.
    """

    def __init__(self, ttl_seconds: float = TICKET_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._tickets: dict[str, DownloadTicket] = {}
        self._lock = threading.Lock()

    def issue(self, device_id: str, paths: Sequence[str], filename: str) -> str:
        token = secrets.token_urlsafe(24)
        with self._lock:
            self._purge()
            self._tickets[token] = DownloadTicket(
                device_id=device_id,
                paths=tuple(paths),
                filename=filename,
                expires_at=time.monotonic() + self.ttl_seconds,
            )
        return token

    def redeem(self, token: str) -> DownloadTicket | None:
        with self._lock:
            self._purge()
            ticket = self._tickets.pop(token, None)
        if ticket and ticket.expires_at >= time.monotonic():
            return ticket
        return None

    def _purge(self) -> None:
        now = time.monotonic()
        for token in [t for t, v in self._tickets.items() if v.expires_at < now]:
            del self._tickets[token]
