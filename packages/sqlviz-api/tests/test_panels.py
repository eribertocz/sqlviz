"""Tests for /api/v1/panels CRUD endpoints.

Design decision: creating a panel with a non-existent dashboard_id returns 404.
The dashboard is a required parent resource; its absence is "not found."
"""

from __future__ import annotations

from fastapi.testclient import TestClient

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_dashboard(client: TestClient, name: str = "D") -> str:
    return client.post("/api/v1/dashboards", json={"name": name}).json()["id"]


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreatePanel:

    def test_returns_201(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        resp = client.post(
            "/api/v1/panels",
            json={"dashboard_id": dash_id, "name": "P1"},
        )
        assert resp.status_code == 201

    def test_response_has_id(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        resp = client.post(
            "/api/v1/panels",
            json={"dashboard_id": dash_id, "name": "P1"},
        )
        data = resp.json()
        assert "id" in data and len(data["id"]) > 0

    def test_response_fields(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        resp = client.post(
            "/api/v1/panels",
            json={"dashboard_id": dash_id, "name": "Revenue", "sql_content": "SELECT 1"},
        )
        data = resp.json()
        assert data["dashboard_id"] == dash_id
        assert data["name"] == "Revenue"
        assert data["sql_content"] == "SELECT 1"
        assert data["sort_order"] == 0
        assert "created_at" in data

    def test_nonexistent_dashboard_returns_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/panels",
            json={"dashboard_id": "does-not-exist", "name": "P"},
        )
        assert resp.status_code == 404

    def test_default_sql_content_is_empty(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        resp = client.post(
            "/api/v1/panels",
            json={"dashboard_id": dash_id, "name": "Empty"},
        )
        assert resp.json()["sql_content"] == ""


# ── Get ───────────────────────────────────────────────────────────────────────

class TestGetPanel:

    def test_get_existing_returns_200(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        panel_id = client.post(
            "/api/v1/panels", json={"dashboard_id": dash_id, "name": "P"}
        ).json()["id"]
        resp = client.get(f"/api/v1/panels/{panel_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "P"

    def test_get_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/panels/does-not-exist")
        assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdatePanel:

    def test_patch_sql_content(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        panel_id = client.post(
            "/api/v1/panels", json={"dashboard_id": dash_id, "name": "P"}
        ).json()["id"]
        resp = client.patch(
            f"/api/v1/panels/{panel_id}",
            json={"sql_content": "SELECT revenue FROM sales"},
        )
        assert resp.status_code == 200
        assert resp.json()["sql_content"] == "SELECT revenue FROM sales"

    def test_patch_name(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        panel_id = client.post(
            "/api/v1/panels", json={"dashboard_id": dash_id, "name": "Old"}
        ).json()["id"]
        updated = client.patch(
            f"/api/v1/panels/{panel_id}", json={"name": "New"}
        ).json()
        assert updated["name"] == "New"

    def test_patch_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.patch("/api/v1/panels/nope", json={"name": "X"})
        assert resp.status_code == 404

    def test_patch_updates_updated_at(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        created = client.post(
            "/api/v1/panels", json={"dashboard_id": dash_id, "name": "P"}
        ).json()
        updated = client.patch(
            f"/api/v1/panels/{created['id']}", json={"name": "P2"}
        ).json()
        assert updated["updated_at"] >= created["created_at"]


# ── Delete ────────────────────────────────────────────────────────────────────

class TestDeletePanel:

    def test_delete_returns_204(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        panel_id = client.post(
            "/api/v1/panels", json={"dashboard_id": dash_id, "name": "P"}
        ).json()["id"]
        resp = client.delete(f"/api/v1/panels/{panel_id}")
        assert resp.status_code == 204

    def test_deleted_panel_returns_404(self, client: TestClient) -> None:
        dash_id = _make_dashboard(client)
        panel_id = client.post(
            "/api/v1/panels", json={"dashboard_id": dash_id, "name": "P"}
        ).json()["id"]
        client.delete(f"/api/v1/panels/{panel_id}")
        resp = client.get(f"/api/v1/panels/{panel_id}")
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/panels/nope")
        assert resp.status_code == 404
