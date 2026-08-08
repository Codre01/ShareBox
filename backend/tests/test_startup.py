from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sharebox.app import startup, startup_linux

linux_only = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="XDG autostart is Linux-specific",
)


@pytest.fixture()
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


def test_autostart_dir_follows_xdg_config_home(xdg_home: Path):
    assert startup_linux.autostart_dir() == xdg_home / "autostart"


def test_enable_writes_desktop_entry(xdg_home: Path):
    startup_linux.set_launch_at_startup(True)

    entry = xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME
    content = entry.read_text(encoding="utf-8")
    assert content.startswith("[Desktop Entry]")
    assert "Name=ShareBox" in content
    assert "Exec=" in content
    assert "Terminal=false" in content


def test_enable_accepts_explicit_command(xdg_home: Path):
    startup_linux.set_launch_at_startup(True, command="/opt/sharebox/ShareBox")

    entry = xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME
    assert "Exec=/opt/sharebox/ShareBox" in entry.read_text(encoding="utf-8")


def test_disable_removes_desktop_entry(xdg_home: Path):
    startup_linux.set_launch_at_startup(True)
    entry = xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME
    assert entry.exists()

    startup_linux.set_launch_at_startup(False)
    assert not entry.exists()


def test_disable_is_a_no_op_when_never_enabled(xdg_home: Path):
    startup_linux.set_launch_at_startup(False)  # must not raise
    assert not (xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME).exists()


def test_enable_is_idempotent(xdg_home: Path):
    startup_linux.set_launch_at_startup(True, command="/opt/sharebox/ShareBox")
    startup_linux.set_launch_at_startup(True, command="/opt/sharebox/ShareBox")

    entry = xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME
    assert entry.read_text(encoding="utf-8").count("[Desktop Entry]") == 1


@linux_only
def test_dispatcher_routes_to_linux_implementation(xdg_home: Path):
    startup.set_launch_at_startup(True)
    assert (xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME).exists()

    startup.set_launch_at_startup(False)
    assert not (xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME).exists()


def test_dispatcher_reports_support_for_this_platform():
    expected = sys.platform == "win32" or sys.platform.startswith("linux")
    assert startup.supports_launch_at_startup() is expected


def test_dispatcher_is_a_no_op_on_unsupported_platforms(
    xdg_home: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(sys, "platform", "darwin")
    startup.set_launch_at_startup(True)  # must not raise
    assert not (xdg_home / "autostart" / startup_linux.DESKTOP_FILE_NAME).exists()
