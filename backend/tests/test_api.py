from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sharebox.app.main import create_app


@pytest.fixture()
def client(tmp_path: Path):
    app_data = tmp_path / "appdata"
    shared = tmp_path / "ShareBox"
    shared.mkdir()
    (shared / "hello.txt").write_text("hello from host", encoding="utf-8")
    (shared / "docs").mkdir()
    (shared / "docs" / "note.txt").write_text("nested", encoding="utf-8")

    app = create_app(app_data)
    # Point shared folder at temp.
    ctx = app.state.sharebox_ctx
    ctx.config.update(shared_folder=str(shared))
    ctx.fs.set_root(shared)

    with TestClient(app) as c:
        yield c, ctx, shared


def _pair(client: TestClient, name: str = "Test Phone") -> str:
    start = client.post("/api/v1/pairing/start").json()
    done = client.post(
        "/api/v1/pairing/complete",
        json={"token": start["token"], "display_name": name},
    )
    assert done.status_code == 200, done.text
    return done.json()["device_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    c, _, _ = client
    r = c.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_unauthorized_files(client):
    c, _, _ = client
    r = c.get("/api/v1/files")
    assert r.status_code == 401


def test_pairing_and_list(client):
    c, _, _ = client
    token = _pair(c)
    r = c.get("/api/v1/files", headers=_auth(token))
    assert r.status_code == 200
    names = {i["name"] for i in r.json()["items"]}
    assert "hello.txt" in names
    assert "docs" in names


def test_path_traversal_rejected(client):
    c, _, _ = client
    token = _pair(c)
    r = c.get("/api/v1/files", params={"path": "../"}, headers=_auth(token))
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "PATH_ESCAPE"


def test_download(client):
    c, _, _ = client
    token = _pair(c)
    r = c.get("/api/v1/files/download", params={"path": "hello.txt"}, headers=_auth(token))
    assert r.status_code == 200
    assert r.content == b"hello from host"


def test_upload_lazy_device_folder_and_collision(client):
    c, ctx, shared = client
    token = _pair(c, name="Pixel")
    # First upload creates device folder.
    assert not (shared / "Pixel").exists()
    files = [("files", ("photo.jpg", io.BytesIO(b"img1"), "image/jpeg"))]
    r = c.post("/api/v1/files/upload", files=files, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert (shared / "Pixel" / "photo.jpg").exists()

    # Collision rename
    files = [("files", ("photo.jpg", io.BytesIO(b"img2"), "image/jpeg"))]
    r = c.post("/api/v1/files/upload", files=files, headers=_auth(token))
    assert r.status_code == 200
    assert (shared / "Pixel" / "photo (1).jpg").exists()


def test_revocation_blocks_access(client):
    c, ctx, _ = client
    token = _pair(c)
    devices = c.get("/api/v1/devices").json()["devices"]
    device_id = devices[0]["device_id"]
    assert c.get("/api/v1/files", headers=_auth(token)).status_code == 200
    rev = c.delete(f"/api/v1/devices/{device_id}")
    assert rev.status_code == 200
    assert c.get("/api/v1/files", headers=_auth(token)).status_code == 401


def test_pairing_token_single_use(client):
    c, _, _ = client
    start = c.post("/api/v1/pairing/start").json()
    first = c.post(
        "/api/v1/pairing/complete",
        json={"token": start["token"], "display_name": "A"},
    )
    assert first.status_code == 200
    second = c.post(
        "/api/v1/pairing/complete",
        json={"token": start["token"], "display_name": "B"},
    )
    assert second.status_code == 410


def test_search(client):
    c, _, _ = client
    token = _pair(c)
    r = c.get("/api/v1/files/search", params={"q": "note"}, headers=_auth(token))
    assert r.status_code == 200
    assert any(i["name"] == "note.txt" for i in r.json()["items"])


def test_subfolder_list(client):
    c, _, _ = client
    token = _pair(c)
    r = c.get("/api/v1/files", params={"path": "docs"}, headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["items"][0]["name"] == "note.txt"
