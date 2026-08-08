from __future__ import annotations

import io
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

    app = create_app(app_data)
    ctx = app.state.sharebox_ctx
    ctx.config.update(shared_folder=str(shared))
    ctx.fs.set_root(shared)

    with TestClient(app) as c:
        yield c, ctx, shared


def _upload(c: TestClient, token: str, name: str, data: bytes = b"payload"):
    return c.post(
        "/api/v1/files/upload",
        files=[("files", (name, io.BytesIO(data), "text/plain"))],
        headers=_auth(token),
    )


def test_history_starts_empty(client):
    c, _, _ = client
    token = _pair(c)
    assert c.get("/api/v1/transfers", headers=_auth(token)).json()["items"] == []


def test_upload_is_recorded(client):
    c, _, _ = client
    token = _pair(c)
    assert _upload(c, token, "note.txt", b"12345").status_code == 200

    items = c.get("/api/v1/transfers", headers=_auth(token)).json()["items"]
    assert len(items) == 1
    assert items[0]["direction"] == "upload"
    assert items[0]["name"] == "note.txt"
    assert items[0]["size"] == 5
    assert items[0]["device_label"] == "Test Phone"


def test_download_is_recorded(client):
    c, _, _ = client
    token = _pair(c)
    assert c.get(
        "/api/v1/files/download", params={"path": "hello.txt"}, headers=_auth(token)
    ).status_code == 200

    items = c.get("/api/v1/transfers", headers=_auth(token)).json()["items"]
    assert [i["direction"] for i in items] == ["download"]
    assert items[0]["name"] == "hello.txt"


def test_newest_transfer_comes_first(client):
    c, _, _ = client
    token = _pair(c)
    _upload(c, token, "first.txt")
    _upload(c, token, "second.txt")

    names = [i["name"] for i in c.get("/api/v1/transfers", headers=_auth(token)).json()["items"]]
    assert names == ["second.txt", "first.txt"]


def test_unrecognised_token_on_loopback_falls_back_to_the_host_view(client):
    c, _, _ = client
    # require_device_or_host treats loopback as the host, so a bad token there
    # is the Control Center, not an intruder — the LAN path still gets a 401.
    r = c.get("/api/v1/transfers", headers={"Authorization": "Bearer nope"})
    assert r.json()["scope"] == "all"


def test_device_sees_only_its_own_transfers(client):
    c, ctx, _ = client
    first = _pair(c, "Phone A")
    _upload(c, first, "from-a.txt")

    second = _pair(c, "Phone B")
    _upload(c, second, "from-b.txt")

    a_items = c.get("/api/v1/transfers", headers=_auth(first)).json()
    assert a_items["scope"] == "device"
    assert [i["name"] for i in a_items["items"]] == ["from-a.txt"]

    b_items = c.get("/api/v1/transfers", headers=_auth(second)).json()
    assert [i["name"] for i in b_items["items"]] == ["from-b.txt"]


def test_host_sees_every_device(client):
    c, _, _ = client
    first = _pair(c, "Phone A")
    _upload(c, first, "from-a.txt")
    second = _pair(c, "Phone B")
    _upload(c, second, "from-b.txt")

    host = c.get("/api/v1/transfers").json()
    assert host["scope"] == "all"
    assert {i["name"] for i in host["items"]} == {"from-a.txt", "from-b.txt"}


def test_limit_is_honoured(client):
    c, _, _ = client
    token = _pair(c)
    for index in range(5):
        _upload(c, token, f"f{index}.txt")

    items = c.get("/api/v1/transfers", params={"limit": 2}, headers=_auth(token)).json()["items"]
    assert len(items) == 2


def test_limit_is_bounded(client):
    c, _, _ = client
    token = _pair(c)
    assert c.get(
        "/api/v1/transfers", params={"limit": 10_000}, headers=_auth(token)
    ).status_code == 422


def test_host_can_clear_history(client):
    c, _, _ = client
    token = _pair(c)
    _upload(c, token, "note.txt")

    cleared = c.delete("/api/v1/transfers")
    assert cleared.status_code == 200
    assert cleared.json()["removed"] == 1
    assert c.get("/api/v1/transfers").json()["items"] == []


def test_history_is_capped(client, monkeypatch: pytest.MonkeyPatch):
    c, ctx, _ = client
    monkeypatch.setattr("sharebox.app.api.MAX_TRANSFER_HISTORY", 3)
    token = _pair(c)
    for index in range(6):
        _upload(c, token, f"f{index}.txt")

    items = c.get("/api/v1/transfers", headers=_auth(token)).json()["items"]
    assert len(items) == 3
    assert [i["name"] for i in items] == ["f5.txt", "f4.txt", "f3.txt"]


def test_revoked_device_history_survives_for_the_host(client):
    c, ctx, _ = client
    token = _pair(c)
    _upload(c, token, "note.txt")

    ctx.db.revoke_device(ctx.db.list_devices()[0].device_id)
    assert len(c.get("/api/v1/transfers").json()["items"]) == 1
