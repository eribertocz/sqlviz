"""Tests for POST /api/v1/compose.

Validates that the compose endpoint correctly runs DashboardEngine on
provided InferenceResults and returns a DashboardLayout with KPI Shelf
centering and narrative ordering applied.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _execute(client: TestClient, sql: str) -> dict:
    """Helper: create panel, execute it, return the full execute response body."""
    dash_id = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    panel_id = client.post("/api/v1/panels", json={
        "dashboard_id": dash_id, "name": "P", "sql_content": sql,
    }).json()["id"]
    return client.post(f"/api/v1/panels/{panel_id}/execute").json()


def _ir(client: TestClient, sql: str) -> dict:
    return _execute(client, sql)["inference_result"]


# ── Basic shape ───────────────────────────────────────────────────────────────

class TestComposeShape:

    def test_empty_body_returns_empty_layout(self, client: TestClient) -> None:
        resp = client.post("/api/v1/compose", json=[])
        assert resp.status_code == 200
        assert resp.json()["rows"] == []

    def test_single_panel_returns_one_row(self, client: TestClient) -> None:
        ir = _ir(client, "SELECT SUM(v) AS total FROM (VALUES (1)) t(v)")
        body = client.post("/api/v1/compose", json=[
            {"panel_id": "p1", "inference_result": ir}
        ]).json()
        assert len(body["rows"]) == 1
        assert len(body["rows"][0]["panels"]) == 1

    def test_panel_id_preserved_in_response(self, client: TestClient) -> None:
        ir = _ir(client, "SELECT SUM(v) AS total FROM (VALUES (1)) t(v)")
        body = client.post("/api/v1/compose", json=[
            {"panel_id": "custom-id-xyz", "inference_result": ir}
        ]).json()
        assert body["rows"][0]["panels"][0]["panel_id"] == "custom-id-xyz"

    def test_data_is_empty_list_in_response(self, client: TestClient) -> None:
        ir = _ir(client, "SELECT SUM(v) AS total FROM (VALUES (1)) t(v)")
        body = client.post("/api/v1/compose", json=[
            {"panel_id": "p1", "inference_result": ir}
        ]).json()
        assert body["rows"][0]["panels"][0]["data"] == []

    def test_inference_result_returned_unchanged(self, client: TestClient) -> None:
        ir = _ir(client, "SELECT SUM(v) AS total FROM (VALUES (1)) t(v)")
        body = client.post("/api/v1/compose", json=[
            {"panel_id": "p1", "inference_result": ir}
        ]).json()
        returned_ir = body["rows"][0]["panels"][0]["inference_result"]
        assert returned_ir["chart_winner"] == ir["chart_winner"]
        assert returned_ir["intent_winner"] == ir["intent_winner"]


# ── KPI Shelf layout ──────────────────────────────────────────────────────────

class TestComposeKPIShelf:

    def _kpi_ir(self, client: TestClient) -> dict:
        return _ir(client, "SELECT SUM(v) AS total FROM (VALUES (42)) t(v)")

    def test_one_kpi_gets_span4_offset4(self, client: TestClient) -> None:
        ir = self._kpi_ir(client)
        body = client.post("/api/v1/compose", json=[
            {"panel_id": "p1", "inference_result": ir}
        ]).json()
        panel = body["rows"][0]["panels"][0]
        assert panel["final_col_span"] == 4
        assert panel["col_offset"] == 4

    def test_two_kpis_get_offset2_and_0(self, client: TestClient) -> None:
        ir = self._kpi_ir(client)
        body = client.post("/api/v1/compose", json=[
            {"panel_id": "p1", "inference_result": ir},
            {"panel_id": "p2", "inference_result": ir},
        ]).json()
        panels = body["rows"][0]["panels"]
        assert len(panels) == 2
        assert panels[0]["col_offset"] == 2
        assert panels[1]["col_offset"] == 0

    def test_four_kpis_get_span3(self, client: TestClient) -> None:
        ir = self._kpi_ir(client)
        body = client.post("/api/v1/compose", json=[
            {"panel_id": f"p{i}", "inference_result": ir} for i in range(4)
        ]).json()
        panels = body["rows"][0]["panels"]
        assert len(panels) == 4
        assert all(p["final_col_span"] == 3 for p in panels)
        assert panels[0]["col_offset"] == 0
