"""Shared security helpers for ShareBox API."""

from __future__ import annotations

from fastapi import Request

from sharebox.app.errors import raise_http


def is_loopback(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    return host in {"127.0.0.1", "::1", "localhost", "testclient"}


def require_loopback(request: Request) -> None:
    """Host Control Center / admin APIs must not be reachable from the LAN."""
    if not is_loopback(request):
        raise_http(
            "FORBIDDEN",
            "This action is only available from the ShareBox Control Center on this computer",
            403,
        )


# Upload limits (bytes)
MAX_UPLOAD_FILE_BYTES = 1 * 1024 * 1024 * 1024  # 1 GiB per file
MAX_UPLOAD_REQUEST_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB per request
MAX_CLIPBOARD_CHARS = 64_000
MAX_CLIPBOARD_ITEMS = 20

# How many files/folders a single zip download request may name. The number of
# files they expand to is capped separately by archive.MAX_ARCHIVE_ENTRIES.
MAX_ARCHIVE_SELECTION = 500
