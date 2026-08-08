from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sharebox.app.main import create_app
from test_api import _auth, _pair


@pytest.fixture()
def client(tmp_path: Path):
    app_data = tmp_path / "appdata"
    shared = tmp_path / "ShareBox"
    shared.mkdir()
    (shared / "hello.txt").write_text("hello from host", encoding="utf-8")
    (shared / "docs").mkdir()
    (shared / "docs" / "note.txt").write_text("nested", encoding="utf-8")

    app = create_app(app_data)
    ctx = app.state.sharebox_ctx
    ctx.config.update(shared_folder=str(shared))
    ctx.fs.set_root(shared)

    with TestClient(app) as c:
        yield c, ctx, shared


def _ticket(c: TestClient, token: str, paths: list[str]):
    return c.post(
        "/api/v1/files/archive/ticket",
        json={"paths": paths},
        headers=_auth(token),
    )


def test_ticket_requires_auth(client):
    c, _, _ = client
    assert c.post("/api/v1/files/archive/ticket", json={"paths": ["docs"]}).status_code == 401


def test_download_folder_as_zip(client):
    c, _, _ = client
    token = _pair(c)

    issued = _ticket(c, token, ["docs"])
    assert issued.status_code == 200, issued.text
    body = issued.json()
    assert body["filename"] == "docs.zip"
    assert body["file_count"] == 1

    got = c.get("/api/v1/files/archive", params={"ticket": body["ticket"]})
    assert got.status_code == 200
    assert got.headers["content-type"] == "application/zip"
    assert "docs.zip" in got.headers["content-disposition"]

    archive = zipfile.ZipFile(io.BytesIO(got.content))
    assert archive.read("docs/note.txt") == b"nested"


def test_download_multiple_selected_files(client):
    c, _, _ = client
    token = _pair(c)

    body = _ticket(c, token, ["hello.txt", "docs"]).json()
    assert body["filename"] == "ShareBox files.zip"

    got = c.get("/api/v1/files/archive", params={"ticket": body["ticket"]})
    archive = zipfile.ZipFile(io.BytesIO(got.content))
    assert sorted(archive.namelist()) == ["docs/note.txt", "hello.txt"]


def test_ticket_is_single_use(client):
    c, _, _ = client
    token = _pair(c)
    ticket = _ticket(c, token, ["docs"]).json()["ticket"]

    assert c.get("/api/v1/files/archive", params={"ticket": ticket}).status_code == 200
    assert c.get("/api/v1/files/archive", params={"ticket": ticket}).status_code == 410


def test_unknown_ticket_is_rejected(client):
    c, _, _ = client
    assert c.get("/api/v1/files/archive", params={"ticket": "bogus"}).status_code == 410


def test_ticket_rejects_traversal(client):
    c, _, _ = client
    token = _pair(c)
    assert _ticket(c, token, ["../../etc"]).status_code == 400


def test_ticket_rejects_missing_path(client):
    c, _, _ = client
    token = _pair(c)
    assert _ticket(c, token, ["nope.txt"]).status_code == 404


def test_ticket_rejects_empty_selection(client):
    c, _, _ = client
    token = _pair(c)
    assert _ticket(c, token, []).status_code == 422


def test_revoked_device_cannot_spend_its_ticket(client):
    c, ctx, _ = client
    token = _pair(c)
    ticket = _ticket(c, token, ["docs"]).json()["ticket"]

    device_id = ctx.db.list_devices()[0].device_id
    ctx.db.revoke_device(device_id)

    assert c.get("/api/v1/files/archive", params={"ticket": ticket}).status_code == 401
