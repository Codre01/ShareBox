from __future__ import annotations

from pathlib import Path

import pytest

from sharebox.app.files import (
    FilesystemService,
    PathEscapeError,
    ProtectedPathError,
    TRASH_DIR_NAME,
)


@pytest.fixture()
def fs(tmp_path: Path) -> FilesystemService:
    root = tmp_path / "share"
    root.mkdir()
    (root / "hello.txt").write_text("hello", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.txt").write_text("nested", encoding="utf-8")
    return FilesystemService(root)


class TestDelete:
    def test_file_moves_to_trash_rather_than_vanishing(self, fs: FilesystemService):
        trashed = fs.move_to_trash("hello.txt")

        assert not (fs.root / "hello.txt").exists()
        assert (fs.root / trashed).is_file()
        assert (fs.root / trashed).read_text(encoding="utf-8") == "hello"

    def test_folder_moves_with_its_contents(self, fs: FilesystemService):
        trashed = fs.move_to_trash("docs")

        assert not (fs.root / "docs").exists()
        assert (fs.root / trashed / "note.txt").read_text(encoding="utf-8") == "nested"

    def test_same_name_twice_does_not_clobber(self, fs: FilesystemService):
        first = fs.move_to_trash("hello.txt")
        (fs.root / "hello.txt").write_text("second", encoding="utf-8")
        second = fs.move_to_trash("hello.txt")

        assert first != second
        assert (fs.root / first).read_text(encoding="utf-8") == "hello"
        assert (fs.root / second).read_text(encoding="utf-8") == "second"

    def test_shared_root_is_protected(self, fs: FilesystemService):
        with pytest.raises(ProtectedPathError):
            fs.move_to_trash("")

    def test_trash_itself_is_protected(self, fs: FilesystemService):
        fs.move_to_trash("hello.txt")
        with pytest.raises(ProtectedPathError):
            fs.move_to_trash(TRASH_DIR_NAME)

    def test_items_inside_trash_are_protected(self, fs: FilesystemService):
        trashed = fs.move_to_trash("hello.txt")
        with pytest.raises(ProtectedPathError):
            fs.move_to_trash(trashed)

    def test_traversal_is_rejected(self, fs: FilesystemService):
        with pytest.raises(PathEscapeError):
            fs.move_to_trash("../outside")

    def test_missing_path_raises(self, fs: FilesystemService):
        with pytest.raises(FileNotFoundError):
            fs.move_to_trash("nope.txt")


class TestRename:
    def test_renames_in_place(self, fs: FilesystemService):
        assert fs.rename("hello.txt", "greeting.txt") == "greeting.txt"
        assert (fs.root / "greeting.txt").read_text(encoding="utf-8") == "hello"

    def test_nested_item_keeps_its_folder(self, fs: FilesystemService):
        assert fs.rename("docs/note.txt", "memo.txt") == "docs/memo.txt"

    def test_new_name_cannot_relocate_the_item(self, fs: FilesystemService):
        # Separators are stripped by sanitising, so this cannot escape "docs".
        assert fs.rename("docs/note.txt", "../escaped.txt") == "docs/escaped.txt"
        assert not (fs.root / "escaped.txt").exists()

    def test_collision_is_refused(self, fs: FilesystemService):
        with pytest.raises(FileExistsError):
            fs.rename("hello.txt", "docs")

    def test_renaming_to_the_same_name_is_a_no_op(self, fs: FilesystemService):
        assert fs.rename("hello.txt", "hello.txt") == "hello.txt"
        assert (fs.root / "hello.txt").exists()

    def test_hidden_names_are_made_visible(self, fs: FilesystemService):
        # A dotfile drops out of listings, which looks just like deletion, so
        # the leading dot is stripped rather than honoured.
        assert fs.rename("hello.txt", ".hidden") == "hidden"
        assert "hidden" in {item["name"] for item in fs.list_dir("")}

    def test_shared_root_is_protected(self, fs: FilesystemService):
        with pytest.raises(ProtectedPathError):
            fs.rename("", "newname")

    def test_traversal_is_rejected(self, fs: FilesystemService):
        with pytest.raises(PathEscapeError):
            fs.rename("../outside", "x")


class TestTrashHousekeeping:
    def test_trash_is_hidden_from_listings(self, fs: FilesystemService):
        fs.move_to_trash("hello.txt")
        assert TRASH_DIR_NAME not in {item["name"] for item in fs.list_dir("")}

    def test_trashed_files_do_not_appear_in_search(self, fs: FilesystemService):
        assert any(r["name"] == "hello.txt" for r in fs.search("hello"))
        fs.move_to_trash("hello.txt")
        assert fs.search("hello") == []

    def test_empty_trash_removes_files_and_folders(self, fs: FilesystemService):
        fs.move_to_trash("hello.txt")
        fs.move_to_trash("docs")

        assert len(fs.trash_items()) == 2
        assert fs.empty_trash() == 2
        assert fs.trash_items() == []

    def test_empty_trash_when_never_used(self, fs: FilesystemService):
        assert fs.empty_trash() == 0
        assert fs.trash_items() == []
