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
    req = client.post(
        "/api/v1/pairing/request",
        json={"token": start["token"], "suggested_name": name},
    )
    assert req.status_code == 200, req.text
    body = req.json()
    request_id = body["request_id"]
    claim_secret = body["claim_secret"]
    approved = client.post(
        "/api/v1/pairing/approve",
        json={"request_id": request_id, "display_name": name},
    )
    assert approved.status_code == 200, approved.text
    status = client.get(
        f"/api/v1/pairing/request/{request_id}",
        params={"claim_secret": claim_secret},
    )
    assert status.status_code == 200, status.text
    assert status.json()["status"] == "approved"
    return status.json()["device_token"]


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
        "/api/v1/pairing/request",
        json={"token": start["token"], "suggested_name": "A"},
    )
    assert first.status_code == 200
    request_id = first.json()["request_id"]
    assert (
        c.post(
            "/api/v1/pairing/approve",
            json={"request_id": request_id, "display_name": "Device A"},
        ).status_code
        == 200
    )
    second = c.post(
        "/api/v1/pairing/request",
        json={"token": start["token"], "suggested_name": "B"},
    )
    assert second.status_code == 410


def test_pairing_names_folder_slug(client):
    c, ctx, shared = client
    start = c.post("/api/v1/pairing/start").json()
    req = c.post(
        "/api/v1/pairing/request",
        json={"token": start["token"], "suggested_name": "iPhone"},
    ).json()
    c.post(
        "/api/v1/pairing/approve",
        json={"request_id": req["request_id"], "display_name": "Bolu's iPhone"},
    )
    devices = c.get("/api/v1/devices").json()["devices"]
    assert devices[0]["display_name"] == "Bolu's iPhone"
    assert devices[0]["folder_slug"] == "Bolu's iPhone"
    token = c.get(
        f"/api/v1/pairing/request/{req['request_id']}",
        params={"claim_secret": req["claim_secret"]},
    ).json()["device_token"]
    files = [("files", ("shot.png", io.BytesIO(b"x"), "image/png"))]
    up = c.post("/api/v1/files/upload", files=files, headers=_auth(token))
    assert up.status_code == 200
    assert (shared / "Bolu's iPhone" / "shot.png").exists()


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


def test_rename_device(client):
    c, _, _ = client
    token = _pair(c, name="Phone")
    device_id = c.get("/api/v1/devices").json()["devices"][0]["device_id"]
    r = c.patch(f"/api/v1/devices/{device_id}", json={"display_name": "Kitchen iPad"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "Kitchen iPad"
    # Folder slug stays stable; auth still works
    assert c.get("/api/v1/files", headers=_auth(token)).status_code == 200


def test_clipboard_host_and_device(client):
    c, _, _ = client
    token = _pair(c, name="Phone")
    host = c.post("/api/v1/clipboard", json={"text": "wifi: hazelnut-42"})
    assert host.status_code == 200
    assert host.json()["item"]["source_label"]
    phone = c.post(
        "/api/v1/clipboard",
        json={"text": "https://example.com"},
        headers=_auth(token),
    )
    assert phone.status_code == 200
    items = c.get("/api/v1/clipboard", headers=_auth(token)).json()["items"]
    assert len(items) >= 2
    assert items[0]["text"] == "https://example.com"
    deleted = c.delete(f"/api/v1/clipboard/{items[0]['item_id']}")
    assert deleted.status_code == 200
    left = c.get("/api/v1/clipboard", headers=_auth(token)).json()["items"]
    assert all(i["item_id"] != items[0]["item_id"] for i in left)


def test_clipboard_fifo_max_20(client):
    c, _, _ = client
    token = _pair(c)
    for i in range(25):
        r = c.post("/api/v1/clipboard", json={"text": f"clip-{i}"}, headers=_auth(token))
        assert r.status_code == 200
    items = c.get("/api/v1/clipboard", headers=_auth(token)).json()["items"]
    assert len(items) == 20
    texts = {i["text"] for i in items}
    assert "clip-24" in texts
    assert "clip-0" not in texts
    assert "clip-4" not in texts
    assert "clip-5" in texts


def test_lan_status_hides_pairing_secret(client, monkeypatch):
    c, ctx, _ = client
    c.post("/api/v1/pairing/start")

    monkeypatch.setattr("sharebox.app.api.is_loopback", lambda _request: False)
    monkeypatch.setattr("sharebox.app.security.is_loopback", lambda _request: False)
    status = c.get("/api/v1/status").json()
    assert status.get("active_pairing") is None
    assert "shared_folder" not in status
    assert c.post("/api/v1/pairing/start").status_code == 403
    assert c.get("/api/v1/devices").status_code == 403
    assert c.get("/api/v1/settings").status_code == 403

