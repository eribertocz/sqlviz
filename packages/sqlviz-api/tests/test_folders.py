"""Tests for /api/v1/folders CRUD endpoints.

Covers the cascade-to-root behavior on DELETE:
  - Dashboards inside a deleted folder move to root (folder_id=NULL).
  - Child folders of a deleted folder move to root (parent_id=NULL).
  - Neither dashboards nor sub-folders are deleted along with the folder.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_folder(client: TestClient, name: str = "F", parent_id: str | None = None) -> str:
    body: dict[str, object] = {"name": name}
    if parent_id is not None:
        body["parent_id"] = parent_id
    return client.post("/api/v1/folders", json=body).json()["id"]


def _make_dashboard(client: TestClient, name: str = "D", folder_id: str | None = None) -> str:
    body: dict[str, object] = {"name": name}
    if folder_id is not None:
        body["folder_id"] = folder_id
    return client.post("/api/v1/dashboards", json=body).json()["id"]


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateFolder:

    def test_returns_201(self, client: TestClient) -> None:
        resp = client.post("/api/v1/folders", json={"name": "Reports"})
        assert resp.status_code == 201

    def test_response_has_id(self, client: TestClient) -> None:
        data = client.post("/api/v1/folders", json={"name": "Reports"}).json()
        assert "id" in data and len(data["id"]) > 0

    def test_response_fields(self, client: TestClient) -> None:
        data = client.post(
            "/api/v1/folders", json={"name": "Finance", "sort_order": 3}
        ).json()
        assert data["name"] == "Finance"
        assert data["sort_order"] == 3
        assert data["parent_id"] is None
        assert "created_at" in data

    def test_nested_folder_has_parent_id(self, client: TestClient) -> None:
        parent_id = _make_folder(client, "Parent")
        child = client.post(
            "/api/v1/folders", json={"name": "Child", "parent_id": parent_id}
        ).json()
        assert child["parent_id"] == parent_id


# ── List ──────────────────────────────────────────────────────────────────────

class TestListFolders:

    def test_empty_on_fresh_project(self, client: TestClient) -> None:
        resp = client.get("/api/v1/folders")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_created_folders_appear_in_list(self, client: TestClient) -> None:
        client.post("/api/v1/folders", json={"name": "Alpha"})
        client.post("/api/v1/folders", json={"name": "Beta"})
        names = [f["name"] for f in client.get("/api/v1/folders").json()]
        assert "Alpha" in names
        assert "Beta" in names


# ── Get ───────────────────────────────────────────────────────────────────────

class TestGetFolder:

    def test_get_existing_returns_200(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Reports")
        resp = client.get(f"/api/v1/folders/{folder_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Reports"

    def test_get_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/folders/does-not-exist")
        assert resp.status_code == 404

    def test_get_returns_correct_folder(self, client: TestClient) -> None:
        id_a = _make_folder(client, "A")
        id_b = _make_folder(client, "B")
        assert client.get(f"/api/v1/folders/{id_a}").json()["name"] == "A"
        assert client.get(f"/api/v1/folders/{id_b}").json()["name"] == "B"


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdateFolder:

    def test_patch_name(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Old")
        updated = client.patch(
            f"/api/v1/folders/{folder_id}", json={"name": "New"}
        ).json()
        assert updated["name"] == "New"

    def test_patch_sort_order(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "F")
        updated = client.patch(
            f"/api/v1/folders/{folder_id}", json={"sort_order": 7}
        ).json()
        assert updated["sort_order"] == 7

    def test_patch_parent_id(self, client: TestClient) -> None:
        parent_id = _make_folder(client, "Parent")
        child_id = _make_folder(client, "Child")
        updated = client.patch(
            f"/api/v1/folders/{child_id}", json={"parent_id": parent_id}
        ).json()
        assert updated["parent_id"] == parent_id

    def test_patch_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.patch("/api/v1/folders/nope", json={"name": "X"})
        assert resp.status_code == 404

    def test_patch_empty_body_returns_unchanged(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Stable")
        original = client.get(f"/api/v1/folders/{folder_id}").json()
        updated = client.patch(f"/api/v1/folders/{folder_id}", json={}).json()
        assert updated["name"] == original["name"]


# ── Delete ────────────────────────────────────────────────────────────────────

class TestDeleteFolder:

    def test_delete_returns_204(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Temp")
        resp = client.delete(f"/api/v1/folders/{folder_id}")
        assert resp.status_code == 204

    def test_deleted_folder_not_in_list(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Gone")
        client.delete(f"/api/v1/folders/{folder_id}")
        ids = [f["id"] for f in client.get("/api/v1/folders").json()]
        assert folder_id not in ids

    def test_deleted_folder_returns_404(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Gone")
        client.delete(f"/api/v1/folders/{folder_id}")
        assert client.get(f"/api/v1/folders/{folder_id}").status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/folders/nope")
        assert resp.status_code == 404

    def test_dashboards_inside_move_to_root_on_delete(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Container")
        dash_id = _make_dashboard(client, "Inside", folder_id=folder_id)

        # Verify dashboard is in the folder before deletion
        dash_before = client.get(f"/api/v1/dashboards/{dash_id}").json()
        assert dash_before["folder_id"] == folder_id

        client.delete(f"/api/v1/folders/{folder_id}")

        # Dashboard must still exist and be at root
        dash_after = client.get(f"/api/v1/dashboards/{dash_id}").json()
        assert dash_after["id"] == dash_id
        assert dash_after["folder_id"] is None

    def test_child_folders_move_to_root_on_delete(self, client: TestClient) -> None:
        parent_id = _make_folder(client, "Parent")
        child_id = _make_folder(client, "Child", parent_id=parent_id)

        child_before = client.get(f"/api/v1/folders/{child_id}").json()
        assert child_before["parent_id"] == parent_id

        client.delete(f"/api/v1/folders/{parent_id}")

        # Child folder must still exist and be at root
        child_after = client.get(f"/api/v1/folders/{child_id}").json()
        assert child_after["id"] == child_id
        assert child_after["parent_id"] is None

    def test_multiple_dashboards_move_to_root_on_delete(self, client: TestClient) -> None:
        folder_id = _make_folder(client, "Folder")
        dash_ids = [_make_dashboard(client, f"D{i}", folder_id=folder_id) for i in range(3)]

        client.delete(f"/api/v1/folders/{folder_id}")

        for dash_id in dash_ids:
            dash = client.get(f"/api/v1/dashboards/{dash_id}").json()
            assert dash["folder_id"] is None
