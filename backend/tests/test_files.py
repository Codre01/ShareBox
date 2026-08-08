from pathlib import Path

from sharebox.app.files import FilesystemService, PathEscapeError
import pytest


def test_resolve_blocks_dotdot(tmp_path: Path):
    fs = FilesystemService(tmp_path)
    with pytest.raises(PathEscapeError):
        fs.resolve("../outside")


def test_unique_name_collision(tmp_path: Path):
    fs = FilesystemService(tmp_path)
    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    assert fs.unique_name(tmp_path, "a.txt").name == "a (1).txt"


def test_sanitize_filename():
    fs = FilesystemService
    assert ".." not in fs.sanitize_filename("../x.txt")
    assert fs.sanitize_filename("a/b\\c.txt") == "c.txt"


def test_sanitize_filename_strips_windows_paths_on_any_host():
    # A Windows browser sends backslash paths even when the host is Linux.
    fs = FilesystemService
    assert fs.sanitize_filename(r"C:\Users\me\report.pdf") == "report.pdf"
    assert fs.sanitize_filename("..\\..\\etc\\passwd") == "passwd"
