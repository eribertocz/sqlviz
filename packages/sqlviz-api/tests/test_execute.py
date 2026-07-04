"""Tests for POST /api/v1/panels/{panel_id}/execute.

Validates the full execute pipeline: SQL → DuckDB → Inference Engine → JSON.
Response shape: {"inference_result": {...}, "data": [...]}.
Error handling: invalid SQL → 200+fallback, missing table → 422, no panel → 404.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _make_panel(client: TestClient, sql: str) -> str:
    dash_id = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    return client.post("/api/v1/panels", json={
        "dashboard_id": dash_id,
        "name": "P",
        "sql_content": sql,
    }).json()["id"]


# ── Error cases ───────────────────────────────────────────────────────────────

class TestExecutePanelErrors:

    def test_nonexistent_panel_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/panels/does-not-exist/execute")
        assert resp.status_code == 404

    def test_invalid_sql_returns_200_with_fallback(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "THIS IS NOT VALID SQL !!!")
        resp = client.post(f"/api/v1/panels/{panel_id}/execute")
        assert resp.status_code == 200
        body = resp.json()
        assert body["inference_result"]["fallback_applied"] is True

    def test_invalid_sql_returns_empty_data(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "THIS IS NOT VALID SQL !!!")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert body["data"] == []

    def test_missing_table_returns_422(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT * FROM this_table_does_not_exist")
        resp = client.post(f"/api/v1/panels/{panel_id}/execute")
        assert resp.status_code == 422


# ── Success cases ─────────────────────────────────────────────────────────────

class TestExecutePanelSuccess:

    def test_valid_sql_returns_200(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 42 AS answer")
        resp = client.post(f"/api/v1/panels/{panel_id}/execute")
        assert resp.status_code == 200

    def test_response_has_inference_result_and_data(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 42 AS answer")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert "inference_result" in body
        assert "data" in body

    def test_valid_sql_fallback_not_applied(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 42 AS answer")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert body["inference_result"]["fallback_applied"] is False

    def test_data_contains_query_result(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 42 AS answer")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert body["data"] == [{"answer": 42}]

    def test_trend_query_intent_winner(self, client: TestClient) -> None:
        sql = (
            "SELECT month, SUM(revenue) AS total "
            "FROM (VALUES (1, 100), (2, 200), (3, 300)) t(month, revenue) "
            "GROUP BY month ORDER BY month"
        )
        panel_id = _make_panel(client, sql)
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert body["inference_result"]["intent_winner"] == "trend"

    def test_trend_query_chart_winner(self, client: TestClient) -> None:
        sql = (
            "SELECT month, SUM(revenue) AS total "
            "FROM (VALUES (1, 100), (2, 200), (3, 300)) t(month, revenue) "
            "GROUP BY month ORDER BY month"
        )
        panel_id = _make_panel(client, sql)
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert body["inference_result"]["chart_winner"] == "line"

    def test_response_has_explanation(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 42 AS answer")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        ir = body["inference_result"]
        assert "explanation" in ir
        assert isinstance(ir["explanation"], list)

    def test_response_has_score_trace(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 42 AS answer")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        ir = body["inference_result"]
        assert "score_trace" in ir
        assert isinstance(ir["score_trace"], dict)

    def test_decimal_aggregates_are_serializable(self, client: TestClient) -> None:
        # DuckDB returns Decimal for SUM — must be converted to float
        sql = "SELECT SUM(v) AS total FROM (VALUES (10.5), (20.0)) t(v)"
        panel_id = _make_panel(client, sql)
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert isinstance(body["data"][0]["total"], float)


# ── Variable substitution (Phase 5.7 filter support) ─────────────────────────

class TestExecuteWithVariables:

    def test_integer_variable_is_substituted(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT $n AS val")
        body = client.post(
            f"/api/v1/panels/{panel_id}/execute",
            json={"variables": {"n": 42}},
        ).json()
        assert body["data"] == [{"val": 42}]

    def test_string_variable_is_substituted(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT $name AS greeting")
        body = client.post(
            f"/api/v1/panels/{panel_id}/execute",
            json={"variables": {"name": "Alice"}},
        ).json()
        assert body["data"] == [{"greeting": "Alice"}]

    def test_sql_with_variable_but_no_values_returns_fallback(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT $val AS n")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        assert body["inference_result"]["fallback_applied"] is True
        assert body["data"] == []

    def test_sql_with_variable_and_no_values_populates_filter_controls(
        self, client: TestClient
    ) -> None:
        panel_id = _make_panel(client, "SELECT region FROM regions WHERE region = $region")
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        controls = body["inference_result"]["filter_controls"]
        assert any(c["variable"] == "region" for c in controls)
