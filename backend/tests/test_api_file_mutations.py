from __future__ import annotations

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


def _grant(c: TestClient, ctx) -> None:
    device_id = ctx.db.list_devices()[0].device_id
    r = c.patch(f"/api/v1/devices/{device_id}", json={"can_modify": True})
    assert r.status_code == 200, r.text
    assert r.json()["can_modify"] is True


def test_new_device_cannot_modify_by_default(client):
    c, ctx, shared = client
    token = _pair(c)

    assert ctx.db.list_devices()[0].can_modify is False
    r = c.post("/api/v1/files/delete", json={"path": "hello.txt"}, headers=_auth(token))
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == "MODIFY_FORBIDDEN"
    assert (shared / "hello.txt").exists()


def test_delete_requires_auth(client):
    c, _, _ = client
    assert c.post("/api/v1/files/delete", json={"path": "hello.txt"}).status_code == 401


def test_granted_device_can_delete(client):
    c, ctx, shared = client
    token = _pair(c)
    _grant(c, ctx)

    r = c.post("/api/v1/files/delete", json={"path": "hello.txt"}, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "trashed"
    assert not (shared / "hello.txt").exists()
    # Recoverable, not destroyed.
    assert (shared / r.json()["trash_path"]).read_text(encoding="utf-8") == "hello from host"


def test_granted_device_can_rename(client):
    c, ctx, shared = client
    token = _pair(c)
    _grant(c, ctx)

    r = c.post(
        "/api/v1/files/rename",
        json={"path": "hello.txt", "new_name": "greeting.txt"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["path"] == "greeting.txt"
    assert (shared / "greeting.txt").exists()


def test_permission_can_be_revoked_again(client):
    c, ctx, shared = client
    token = _pair(c)
    _grant(c, ctx)

    device_id = ctx.db.list_devices()[0].device_id
    c.patch(f"/api/v1/devices/{device_id}", json={"can_modify": False})

    r = c.post("/api/v1/files/delete", json={"path": "hello.txt"}, headers=_auth(token))
    assert r.status_code == 403
    assert (shared / "hello.txt").exists()


def test_renaming_a_device_leaves_its_permission_alone(client):
    c, ctx, _ = client
    _pair(c)
    _grant(c, ctx)

    device_id = ctx.db.list_devices()[0].device_id
    r = c.patch(f"/api/v1/devices/{device_id}", json={"display_name": "Kitchen iPad"})
    assert r.json()["display_name"] == "Kitchen iPad"
    assert r.json()["can_modify"] is True


def test_delete_rejects_traversal(client):
    c, ctx, _ = client
    token = _pair(c)
    _grant(c, ctx)

    r = c.post("/api/v1/files/delete", json={"path": "../../etc"}, headers=_auth(token))
    assert r.status_code == 400


def test_delete_rejects_the_shared_root(client):
    c, ctx, shared = client
    token = _pair(c)
    _grant(c, ctx)

    r = c.post("/api/v1/files/delete", json={"path": "/"}, headers=_auth(token))
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "PROTECTED_PATH"
    assert shared.exists()


def test_rename_collision_returns_conflict(client):
    c, ctx, _ = client
    token = _pair(c)
    _grant(c, ctx)

    r = c.post(
        "/api/v1/files/rename",
        json={"path": "hello.txt", "new_name": "docs"},
        headers=_auth(token),
    )
    assert r.status_code == 409


def test_trash_endpoints_are_host_only(client):
    c, ctx, _ = client
    token = _pair(c)
    _grant(c, ctx)
    c.post("/api/v1/files/delete", json={"path": "hello.txt"}, headers=_auth(token))

    # TestClient is treated as loopback, so the host view works...
    listed = c.get("/api/v1/files/trash")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    emptied = c.delete("/api/v1/files/trash")
    assert emptied.json()["removed"] == 1
    assert c.get("/api/v1/files/trash").json()["items"] == []


def test_deleted_file_leaves_the_listing(client):
    c, ctx, _ = client
    token = _pair(c)
    _grant(c, ctx)
    c.post("/api/v1/files/delete", json={"path": "hello.txt"}, headers=_auth(token))

    names = {i["name"] for i in c.get("/api/v1/files", headers=_auth(token)).json()["items"]}
    assert "hello.txt" not in names
    assert ".sharebox-trash" not in names
