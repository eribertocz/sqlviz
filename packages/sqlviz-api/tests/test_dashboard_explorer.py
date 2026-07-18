"""Backend support for the Dashboard Explorer (v0.2.7).

Covers the dashboard `description` field and moving a dashboard between
folders (groups), including moving back to root via folder_id="".
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_dashboard_with_description(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D", "description": "hi"}).json()
    assert d["description"] == "hi"


def test_description_defaults_to_none(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    assert d["description"] is None


def test_patch_description(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()
    upd = client.patch(f"/api/v1/dashboards/{d['id']}", json={"description": "world"}).json()
    assert upd["description"] == "world"


def test_patch_empty_description_clears_it(client: TestClient) -> None:
    d = client.post("/api/v1/dashboards", json={"name": "D", "description": "x"}).json()
    upd = client.patch(f"/api/v1/dashboards/{d['id']}", json={"description": ""}).json()
    assert upd["description"] is None


def test_move_dashboard_between_and_to_root(client: TestClient) -> None:
    f = client.post("/api/v1/folders", json={"name": "Group A"}).json()
    d = client.post("/api/v1/dashboards", json={"name": "D"}).json()

    moved = client.patch(f"/api/v1/dashboards/{d['id']}", json={"folder_id": f["id"]}).json()
    assert moved["folder_id"] == f["id"]

    # Empty string moves back to root (folder_id NULL).
    rooted = client.patch(f"/api/v1/dashboards/{d['id']}", json={"folder_id": ""}).json()
    assert rooted["folder_id"] is None


def test_list_reflects_description_and_folder(client: TestClient) -> None:
    f = client.post("/api/v1/folders", json={"name": "G"}).json()
    client.post(
        "/api/v1/dashboards",
        json={"name": "D", "description": "desc", "folder_id": f["id"]},
    )
    rows = client.get("/api/v1/dashboards").json()
    row = next(r for r in rows if r["name"] == "D")
    assert row["description"] == "desc"
    assert row["folder_id"] == f["id"]
