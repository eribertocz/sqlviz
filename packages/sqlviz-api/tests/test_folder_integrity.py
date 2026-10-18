"""Hierarchy invariants, PATCH presence and placement through authorized HTTP."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlviz_storage.folder_repository import folder_tree_write


def folder(client, name="Folder", parent=None):
    response = client.post("/api/v1/folders", json={"name": name, "parent_id": parent})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def dashboard(client, parent=None):
    response = client.post("/api/v1/dashboards", json={"name": "Dash", "folder_id": parent})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def rows(client):
    conn = client.app.state.db_conn
    return {table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("folders", "dashboards", "_sqlviz_meta")}


@pytest.mark.parametrize("parent", [None, ""])
def test_explicit_null_or_legacy_empty_parent_detaches_folder(client, parent) -> None:
    root = folder(client, "Root")
    child = folder(client, "Child", root)
    before = client.get(f"/api/v1/folders/{child}").json()
    renamed = client.patch(f"/api/v1/folders/{child}", json={"name": "Renamed"})
    assert renamed.status_code == 200 and renamed.json()["parent_id"] == root
    response = client.patch(f"/api/v1/folders/{child}", json={"parent_id": parent})
    assert response.status_code == 200
    assert response.json()["parent_id"] is None
    assert response.json()["created_at"] == before["created_at"]
    assert response.json()["name"] == "Renamed"
    assert client.get(f"/api/v1/folders/{root}").status_code == 200


@pytest.mark.parametrize("parent", [None, ""])
def test_dashboard_omission_preserves_folder_and_explicit_null_detaches(client, parent) -> None:
    root = folder(client, "Root")
    item = dashboard(client, root)
    assert client.patch(f"/api/v1/dashboards/{item}", json={"name": "Renamed"}).json()[
        "folder_id"
    ] == root
    response = client.patch(f"/api/v1/dashboards/{item}", json={"folder_id": parent})
    assert response.status_code == 200 and response.json()["folder_id"] is None
    assert response.json()["name"] == "Renamed"


@pytest.mark.parametrize("operation", ["folder_create", "folder_move", "dash_create", "dash_move"])
def test_missing_destination_returns_422_and_leaves_entire_write_unchanged(
    client, operation,
) -> None:
    root = folder(client, "Root")
    item = dashboard(client, root)
    before = rows(client)
    if operation == "folder_create":
        response = client.post("/api/v1/folders", json={"name": "Bad", "parent_id": "missing"})
    elif operation == "folder_move":
        response = client.patch(f"/api/v1/folders/{root}", json={
            "name": "Must not change", "parent_id": "missing",
        })
    elif operation == "dash_create":
        response = client.post("/api/v1/dashboards", json={"name": "Bad", "folder_id": "missing"})
    else:
        response = client.patch(f"/api/v1/dashboards/{item}", json={
            "name": "Must not change", "folder_id": "missing",
        })
    assert response.status_code == 422
    assert response.json()["code"] == "folder_parent_not_found"
    assert rows(client) == before


@pytest.mark.parametrize("depth", [0, 1, 4])
def test_self_and_descendant_parent_rejected_with_no_partial_changes(client, depth) -> None:
    root = folder(client, "Root")
    descendant = root
    for i in range(depth):
        descendant = folder(client, f"Child {i}", descendant)
    before = rows(client)
    response = client.patch(f"/api/v1/folders/{root}", json={
        "parent_id": descendant, "name": "Must not change", "sort_order": 7,
    })
    assert response.status_code == 422 and response.json()["code"] == "folder_cycle"
    assert rows(client) == before


@pytest.mark.parametrize("body", [
    {"name": None}, {"sort_order": None}, {"name": ""}, {"name": "  "},
    {"parent_id": True}, {"parent_id": 1}, {"parent_id": []},
    {"sort_order": True}, {"sort_order": "3"}, {"sort_order": 2**31},
    {"sort_order": -(2**31) - 1}, {"extra": "ignored?"},
])
def test_invalid_folder_patch_returns_422_without_changes(client, body) -> None:
    target = folder(client)
    before = rows(client)
    response = client.patch(f"/api/v1/folders/{target}", json=body)
    assert response.status_code == 422
    assert rows(client) == before


@pytest.mark.parametrize("body", [
    {"name": None}, {"name": ""}, {"name": "  "},
    {"name": "Folder", "parent_id": {}},
    {"name": "Folder", "sort_order": True},
    {"name": "Folder", "sort_order": 2**31},
    {"name": "Folder", "extra": "ignored?"},
])
def test_invalid_folder_create_returns_422_without_changes(client, body) -> None:
    before = rows(client)
    assert client.post("/api/v1/folders", json=body).status_code == 422
    assert rows(client) == before


def test_empty_patch_is_a_read_and_does_not_change_revision(client) -> None:
    target = folder(client)
    before = rows(client)
    response = client.patch(f"/api/v1/folders/{target}", json={})
    assert response.status_code == 200
    assert rows(client) == before


def test_corrupt_destination_rejected_but_explicit_detach_can_repair(client) -> None:
    a, b, root = folder(client, "A"), folder(client, "B"), folder(client, "Root")
    conn = client.app.state.db_conn
    conn.execute("UPDATE folders SET parent_id = ? WHERE id = ?", [b, a])
    conn.execute("UPDATE folders SET parent_id = ? WHERE id = ?", [a, b])
    before = rows(client)
    response = client.patch(f"/api/v1/folders/{root}", json={"parent_id": a})
    assert response.status_code == 409 and response.json()["code"] == "folder_hierarchy_invalid"
    assert rows(client) == before
    assert client.patch(f"/api/v1/folders/{a}", json={"parent_id": None}).status_code == 200
    assert client.patch(f"/api/v1/folders/{root}", json={"parent_id": b}).status_code == 200


@pytest.mark.parametrize("operation", ["create", "move", "delete", "dash_create", "dash_move"])
def test_http_mutations_conflict_with_an_in_progress_tree_write(client, operation) -> None:
    a, b = folder(client, "A"), folder(client, "B")
    item = dashboard(client)
    cursor = client.app.state.db_conn.cursor()

    def request():
        if operation == "create":
            return client.post("/api/v1/folders", json={"name": "New", "parent_id": a})
        if operation == "move":
            return client.patch(f"/api/v1/folders/{b}", json={"parent_id": a})
        if operation == "delete":
            return client.delete(f"/api/v1/folders/{a}")
        if operation == "dash_create":
            return client.post("/api/v1/dashboards", json={"name": "New", "folder_id": a})
        return client.patch(f"/api/v1/dashboards/{item}", json={"folder_id": a})

    try:
        before = rows(client)
        with folder_tree_write(cursor):
            response = request()
            assert response.status_code == 409
            assert response.json()["code"] == "folder_write_conflict"
            assert rows(client) == before  # The writer's revision is uncommitted.
        assert request().status_code == (204 if operation == "delete" else (
            201 if operation in ("create", "dash_create") else 200
        ))
    finally:
        cursor.close()


def test_folder_delete_preserves_dashboard_and_password_share_session(client) -> None:
    root = folder(client, "Root")
    child = folder(client, "Child", root)
    grandchild = folder(client, "Grandchild", child)
    item = dashboard(client, root)
    panel = client.post("/api/v1/panels", json={
        "name": "Sales", "dashboard_id": item, "sql_content": "SELECT 10 AS revenue",
    }).json()["id"]
    share = client.post(f"/api/v1/dashboards/{item}/share", json={
        "mode": "password", "password": "synthetic-password",
    }).json()
    with TestClient(client.app) as viewer:
        session = viewer.post(f"/view/{share['token']}/unlock", json={
            "password": "synthetic-password",
        }).json()["viewer_session"]
        assert client.delete(f"/api/v1/folders/{root}").status_code == 204
        headers = {"X-SQLviz-Share": share["token"], "X-SQLviz-Viewer-Session": session}
        view = viewer.get(f"/view/{share['token']}", headers=headers)
        assert view.status_code == 200 and view.json()["dashboard"]["folder_id"] is None
        assert viewer.post(f"/api/v1/panels/{panel}/execute",
                           headers=headers, json={}).status_code == 200
    assert client.get(f"/api/v1/folders/{child}").json()["parent_id"] is None
    assert client.get(f"/api/v1/folders/{grandchild}").json()["parent_id"] == child


def test_failed_folder_delete_returns_409_and_rolls_back_promotions(client) -> None:
    root = folder(client, "Root")
    folder(client, "Child", root)
    dashboard(client, root)
    conn = client.app.state.db_conn
    conn.execute("CREATE TABLE retained (folder_id VARCHAR REFERENCES folders(id))")
    conn.execute("INSERT INTO retained VALUES (?)", [root])
    before = rows(client)
    response = client.delete(f"/api/v1/folders/{root}")
    assert response.status_code == 409 and response.json()["code"] == "folder_write_conflict"
    assert "retained" not in response.text
    assert rows(client) == before
