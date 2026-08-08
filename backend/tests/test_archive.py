from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from sharebox.app.archive import (
    ArchiveTooLargeError,
    TicketStore,
    archive_filename,
    collect_entries,
    iter_zip,
)
from sharebox.app.files import FilesystemService, PathEscapeError


@pytest.fixture()
def fs(tmp_path: Path) -> FilesystemService:
    root = tmp_path / "share"
    root.mkdir()
    (root / "hello.txt").write_text("hello", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.txt").write_text("nested", encoding="utf-8")
    (root / "docs" / "deep").mkdir()
    (root / "docs" / "deep" / "buried.txt").write_text("deeper", encoding="utf-8")
    (root / "docs" / ".secret").write_text("hidden", encoding="utf-8")
    return FilesystemService(root)


def _read_zip(chunks) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(b"".join(chunks)))


def test_collect_folder_keeps_folder_prefix(fs: FilesystemService):
    names = [e.arcname for e in collect_entries(fs, ["docs"])]
    assert sorted(names) == ["docs/deep/buried.txt", "docs/note.txt"]


def test_collect_single_file_has_bare_name(fs: FilesystemService):
    assert [e.arcname for e in collect_entries(fs, ["hello.txt"])] == ["hello.txt"]


def test_collect_skips_hidden_files(fs: FilesystemService):
    assert not any(".secret" in e.arcname for e in collect_entries(fs, ["docs"]))


def test_collect_rejects_traversal(fs: FilesystemService):
    with pytest.raises(PathEscapeError):
        collect_entries(fs, ["../outside"])


def test_collect_rejects_missing_path(fs: FilesystemService):
    with pytest.raises(FileNotFoundError):
        collect_entries(fs, ["nope.txt"])


def test_collect_deduplicates_colliding_names(fs: FilesystemService):
    (fs.root / "a").mkdir()
    (fs.root / "b").mkdir()
    (fs.root / "a" / "same.txt").write_text("A", encoding="utf-8")
    (fs.root / "b" / "same.txt").write_text("B", encoding="utf-8")

    names = [e.arcname for e in collect_entries(fs, ["a/same.txt", "b/same.txt"])]
    assert len(set(names)) == 2, f"names collided: {names}"


def test_collect_enforces_entry_cap(fs: FilesystemService, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("sharebox.app.archive.MAX_ARCHIVE_ENTRIES", 2)
    bulk = fs.root / "bulk"
    bulk.mkdir()
    for index in range(5):
        (bulk / f"f{index}.txt").write_text("x", encoding="utf-8")

    with pytest.raises(ArchiveTooLargeError):
        collect_entries(fs, ["bulk"])


def test_zip_roundtrip_contents(fs: FilesystemService):
    archive = _read_zip(iter_zip(collect_entries(fs, ["docs", "hello.txt"])))

    assert archive.read("docs/note.txt") == b"nested"
    assert archive.read("docs/deep/buried.txt") == b"deeper"
    assert archive.read("hello.txt") == b"hello"


def test_zip_is_valid_and_streams_in_chunks(fs: FilesystemService):
    big = fs.root / "big.bin"
    big.write_bytes(b"\xab" * (3 * 1024 * 1024))

    chunks = [c for c in iter_zip(collect_entries(fs, ["big.bin"])) if c]
    assert len(chunks) > 1, "large file should stream, not arrive in one blob"

    archive = _read_zip(chunks)
    assert archive.testzip() is None
    assert len(archive.read("big.bin")) == 3 * 1024 * 1024


def test_zip_skips_file_deleted_mid_flight(fs: FilesystemService):
    entries = collect_entries(fs, ["docs", "hello.txt"])
    (fs.root / "hello.txt").unlink()

    archive = _read_zip(iter_zip(entries))
    assert "hello.txt" not in archive.namelist()
    assert archive.read("docs/note.txt") == b"nested"


def test_zip_of_empty_selection_is_a_valid_empty_archive(fs: FilesystemService):
    (fs.root / "blank").mkdir()
    archive = _read_zip(iter_zip(collect_entries(fs, ["blank"])))
    assert archive.namelist() == []


def test_archive_filename(fs: FilesystemService):
    assert archive_filename(fs, ["docs"]) == "docs.zip"
    assert archive_filename(fs, ["a/b/photos"]) == "photos.zip"
    assert archive_filename(fs, ["a.txt", "b.txt"]) == "ShareBox files.zip"


class TestTicketStore:
    def test_redeem_returns_the_issued_ticket(self):
        store = TicketStore()
        token = store.issue("device-1", ["docs"], "docs.zip")

        ticket = store.redeem(token)
        assert ticket is not None
        assert ticket.device_id == "device-1"
        assert ticket.paths == ("docs",)

    def test_ticket_is_single_use(self):
        store = TicketStore()
        token = store.issue("device-1", ["docs"], "docs.zip")

        assert store.redeem(token) is not None
        assert store.redeem(token) is None

    def test_expired_ticket_is_rejected(self):
        store = TicketStore(ttl_seconds=-1)
        token = store.issue("device-1", ["docs"], "docs.zip")
        assert store.redeem(token) is None

    def test_unknown_ticket_is_rejected(self):
        assert TicketStore().redeem("nope") is None
