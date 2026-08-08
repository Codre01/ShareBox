from __future__ import annotations

import re
from pathlib import Path


INVALID_FOLDER_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class PathEscapeError(ValueError):
    """Raised when a client path would escape the shared root."""


class FilesystemService:
    """Resolves and validates paths inside the ShareBox shared folder."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def set_root(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative: str | None = None) -> Path:
        rel = (relative or "").replace("\\", "/").strip("/")
        if rel in ("", "."):
            candidate = self.root
        else:
            parts = [p for p in rel.split("/") if p not in ("", ".")]
            if any(p == ".." for p in parts):
                raise PathEscapeError("Path traversal is not allowed")
            candidate = self.root.joinpath(*parts)
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise PathEscapeError("Path escapes shared folder") from exc
        if resolved.exists() and resolved.is_symlink():
            # Reject symlinks that point outside the root.
            real = resolved.resolve(strict=True)
            try:
                real.relative_to(self.root)
            except ValueError as exc:
                raise PathEscapeError("Symlink escapes shared folder") from exc
        return resolved

    def list_dir(self, relative: str | None = None) -> list[dict]:
        path = self.resolve(relative)
        if not path.exists():
            raise FileNotFoundError("Folder not found")
        if not path.is_dir():
            raise NotADirectoryError("Not a directory")
        items: list[dict] = []
        for entry in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if entry.name.startswith("."):
                continue
            try:
                if entry.is_symlink():
                    target = entry.resolve(strict=False)
                    target.relative_to(self.root)
            except (ValueError, OSError):
                continue
            stat = entry.stat()
            items.append(
                {
                    "name": entry.name,
                    "type": "folder" if entry.is_dir() else "file",
                    "size": None if entry.is_dir() else stat.st_size,
                    "modified": int(stat.st_mtime),
                    "path": self.relative_path(entry),
                }
            )
        return items

    def relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    def search(self, query: str, limit: int = 200) -> list[dict]:
        q = query.strip().lower()
        if not q:
            return []
        results: list[dict] = []
        for path in self.root.rglob("*"):
            if path.name.startswith("."):
                continue
            try:
                path.resolve().relative_to(self.root)
            except ValueError:
                continue
            if q not in path.name.lower():
                continue
            stat = path.stat()
            results.append(
                {
                    "name": path.name,
                    "type": "folder" if path.is_dir() else "file",
                    "size": None if path.is_dir() else stat.st_size,
                    "modified": int(stat.st_mtime),
                    "path": self.relative_path(path),
                }
            )
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def sanitize_filename(name: str) -> str:
        # Clients send Windows-style paths whatever the host OS is, but Path only
        # treats "\" as a separator on Windows — normalise so a Linux host strips
        # the same leading components a Windows host would.
        name = Path(name.replace("\\", "/")).name
        name = INVALID_FOLDER_CHARS.sub("_", name).strip(" .")
        return name or "untitled"

    @staticmethod
    def slugify_device_folder(display_name: str) -> str:
        base = INVALID_FOLDER_CHARS.sub("_", display_name).strip(" .") or "Device"
        return base[:80]

    def unique_name(self, directory: Path, filename: str) -> Path:
        safe = self.sanitize_filename(filename)
        candidate = directory / safe
        if not candidate.exists():
            return candidate
        stem = Path(safe).stem
        suffix = Path(safe).suffix
        n = 1
        while True:
            alt = directory / f"{stem} ({n}){suffix}"
            if not alt.exists():
                return alt
            n += 1

    def ensure_device_folder(self, folder_slug: str) -> Path:
        folder = self.resolve(folder_slug)
        folder.mkdir(parents=True, exist_ok=True)
        return folder
