"""Tests for /api/v1/dashboards CRUD endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestCreateDashboard:

    def test_returns_201(self, client: TestClient) -> None:
        resp = client.post("/api/v1/dashboards", json={"name": "Sales"})
        assert resp.status_code == 201

    def test_response_has_id(self, client: TestClient) -> None:
        resp = client.post("/api/v1/dashboards", json={"name": "Sales"})
        data = resp.json()
        assert "id" in data and len(data["id"]) > 0

    def test_response_fields(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/dashboards",
            json={"name": "Revenue", "sort_order": 2},
        )
        data = resp.json()
        assert data["name"] == "Revenue"
        assert data["sort_order"] == 2
        assert data["folder_id"] is None
        assert data["connection_id"] is None
        assert "created_at" in data
        assert "updated_at" in data


class TestListDashboards:

    def test_empty_list_on_fresh_project(self, client: TestClient) -> None:
        resp = client.get("/api/v1/dashboards")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_created_dashboards_appear_in_list(self, client: TestClient) -> None:
        client.post("/api/v1/dashboards", json={"name": "Alpha"})
        client.post("/api/v1/dashboards", json={"name": "Beta"})
        resp = client.get("/api/v1/dashboards")
        names = [d["name"] for d in resp.json()]
        assert "Alpha" in names
        assert "Beta" in names


class TestGetDashboard:

    def test_get_existing_returns_200(self, client: TestClient) -> None:
        created = client.post("/api/v1/dashboards", json={"name": "D1"}).json()
        resp = client.get(f"/api/v1/dashboards/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "D1"

    def test_get_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/dashboards/does-not-exist")
        assert resp.status_code == 404

    def test_get_returns_correct_dashboard(self, client: TestClient) -> None:
        id_a = client.post("/api/v1/dashboards", json={"name": "A"}).json()["id"]
        id_b = client.post("/api/v1/dashboards", json={"name": "B"}).json()["id"]
        assert client.get(f"/api/v1/dashboards/{id_a}").json()["name"] == "A"
        assert client.get(f"/api/v1/dashboards/{id_b}").json()["name"] == "B"


class TestUpdateDashboard:

    def test_patch_name_changes_name(self, client: TestClient) -> None:
        created = client.post("/api/v1/dashboards", json={"name": "Old"}).json()
        resp = client.patch(
            f"/api/v1/dashboards/{created['id']}",
            json={"name": "New"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"

    def test_patch_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.patch("/api/v1/dashboards/nope", json={"name": "X"})
        assert resp.status_code == 404

    def test_patch_updates_updated_at(self, client: TestClient) -> None:
        created = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        updated = client.patch(
            f"/api/v1/dashboards/{created['id']}",
            json={"name": "D2"},
        ).json()
        # updated_at must be a valid ISO string and >= created_at
        assert updated["updated_at"] >= created["created_at"]

    def test_patch_sort_order(self, client: TestClient) -> None:
        created = client.post("/api/v1/dashboards", json={"name": "D"}).json()
        updated = client.patch(
            f"/api/v1/dashboards/{created['id']}",
            json={"sort_order": 5},
        ).json()
        assert updated["sort_order"] == 5


class TestDeleteDashboard:

    def test_delete_returns_204(self, client: TestClient) -> None:
        created = client.post("/api/v1/dashboards", json={"name": "Temp"}).json()
        resp = client.delete(f"/api/v1/dashboards/{created['id']}")
        assert resp.status_code == 204

    def test_deleted_dashboard_not_in_list(self, client: TestClient) -> None:
        created = client.post("/api/v1/dashboards", json={"name": "Temp"}).json()
        client.delete(f"/api/v1/dashboards/{created['id']}")
        ids = [d["id"] for d in client.get("/api/v1/dashboards").json()]
        assert created["id"] not in ids

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/dashboards/nope")
        assert resp.status_code == 404
