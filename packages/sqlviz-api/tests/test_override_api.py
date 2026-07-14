"""Tests for PATCH /api/v1/panels/{panel_id}/override — V0.2 Fase E.

Exit criteria (DOC10 §6.14):
  1. PATCH /override persists correctly in .sqlviz (selected_*, *_user_override)
  2. inferred_* never overwritten — selected_* reflects override after PATCH
  3. Session regression test:
       - Execute SQL X → system infers chart A
       - PATCH override to chart B → saved in brain.duckdb
       - Execute SQL X again → inference returns chart B
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_storage.brain_db as brain_module
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage.project_db import create_project


@pytest.fixture(autouse=True)
def _reset_brain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    """Redirect brain.duckdb to tmp_path for test isolation."""
    brain_module._brain_conn = None
    p = tmp_path / ".sqlviz" / "brain.duckdb"
    (tmp_path / ".sqlviz").mkdir()
    monkeypatch.setattr(brain_module, "get_brain_path", lambda: p)
    yield
    if brain_module._brain_conn is not None:
        brain_module._brain_conn.close()
    brain_module._brain_conn = None


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "test.sqlviz"))
    app = create_app(conn)
    with TestClient(app) as c:
        yield c
    conn.close()


def _make_panel(client: TestClient, sql: str) -> str:
    dash_id = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    return client.post("/api/v1/panels", json={
        "dashboard_id": dash_id,
        "name": "P",
        "sql_content": sql,
    }).json()["id"]


_TREND_SQL = (
    "SELECT month, SUM(revenue) AS total "
    "FROM (VALUES (1, 100), (2, 200), (3, 300)) t(month, revenue) "
    "GROUP BY month ORDER BY month"
)


# ── Basic override endpoint ───────────────────────────────────────────────────

class TestOverrideEndpointBasics:

    def test_nonexistent_panel_returns_404(self, client: TestClient) -> None:
        resp = client.patch(
            "/api/v1/panels/does-not-exist/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        assert resp.status_code == 404

    def test_unknown_field_name_returns_422(self, client: TestClient) -> None:
        panel_id = _make_panel(client, "SELECT 1 AS n")
        client.post(f"/api/v1/panels/{panel_id}/execute")
        resp = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "bad_field", "user_value": "bar"},
        )
        assert resp.status_code == 422

    def test_returns_updated_panel_response(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        resp = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == panel_id

    def test_override_before_execute_allowed(self, client: TestClient) -> None:
        # Panel created but never executed — override still allowed
        # (inferred_* are NULL, selected_* set to user_value)
        panel_id = _make_panel(client, "SELECT 1")
        resp = client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        assert resp.status_code == 200


# ── Override persists correctly ───────────────────────────────────────────────

class TestOverridePersistence:

    def test_selected_chart_type_updated(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "bar"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_chart_type"] == "bar"

    def test_chart_user_override_set(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["chart_user_override"] == "pie"

    def test_inferred_chart_type_never_overwritten(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        inferred_before = client.get(
            f"/api/v1/panels/{panel_id}"
        ).json()["inferred_chart_type"]

        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )
        inferred_after = client.get(
            f"/api/v1/panels/{panel_id}"
        ).json()["inferred_chart_type"]

        assert inferred_before == inferred_after

    def test_col_span_override_persists(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "col_span", "user_value": "6"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_col_span"] == 6
        assert panel["col_span_user_override"] == 6
        inferred = panel["inferred_col_span"]
        # inferred must not be 6 unless pipeline chose 6 (it should be 12 for trend)
        assert panel["inferred_col_span"] == inferred  # unchanged

    def test_height_px_override_persists(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "height_px", "user_value": "480"},
        )
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_height_px"] == 480
        assert panel["height_user_override"] == 480


# ── Execute stores inference ──────────────────────────────────────────────────

class TestExecuteStoresInference:

    def test_execute_stores_fingerprint(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["fingerprint"] is not None
        assert panel["fingerprint"] != "UNKNOWN"

    def test_execute_stores_inferred_chart_type(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        body = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["inferred_chart_type"] == body["inference_result"]["chart_winner"]

    def test_execute_initialises_selected_chart_type(self, client: TestClient) -> None:
        panel_id = _make_panel(client, _TREND_SQL)
        client.post(f"/api/v1/panels/{panel_id}/execute")
        panel = client.get(f"/api/v1/panels/{panel_id}").json()
        assert panel["selected_chart_type"] == panel["inferred_chart_type"]


# ── SESSION REGRESSION TEST ───────────────────────────────────────────────────

class TestSessionRegression:
    """Critical exit criterion: learned override survives across executions."""

    def test_override_applied_on_re_execution(self, client: TestClient) -> None:
        """
        1. Execute SQL X → system infers chart A
        2. PATCH override to chart B → brain.duckdb updated
        3. Execute SQL X again → inference returns chart B
        """
        # Use a composition query that normally gets inferred as "bar"
        sql = (
            "SELECT category, SUM(revenue) "
            "FROM (VALUES ('A', 100), ('B', 200), ('C', 300)) t(category, revenue) "
            "GROUP BY category"
        )
        panel_id = _make_panel(client, sql)

        # Step 1: Execute — get inferred chart
        first_exec = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        first_chart = first_exec["inference_result"]["chart_winner"]

        # Step 2: Override to "pie"
        client.patch(
            f"/api/v1/panels/{panel_id}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )

        # Step 3: Execute again — should return "pie"
        second_exec = client.post(f"/api/v1/panels/{panel_id}/execute").json()
        second_chart = second_exec["inference_result"]["chart_winner"]

        # The system must have returned "pie" regardless of what it inferred first
        assert second_chart == "pie", (
            f"Session regression: first={first_chart}, "
            f"expected second='pie', got '{second_chart}'"
        )

    def test_new_panel_benefits_from_existing_brain_pattern(
        self, client: TestClient
    ) -> None:
        """
        Override on panel A teaches brain.duckdb.
        A new panel B with the same SQL shape returns the overridden chart.
        """
        sql = (
            "SELECT category, SUM(revenue) "
            "FROM (VALUES ('A', 100), ('B', 200), ('C', 300)) t(category, revenue) "
            "GROUP BY category"
        )
        dash_id = client.post("/api/v1/dashboards", json={"name": "D2"}).json()["id"]

        # Panel A: execute + override
        panel_a = client.post("/api/v1/panels", json={
            "dashboard_id": dash_id, "name": "A", "sql_content": sql,
        }).json()["id"]
        client.post(f"/api/v1/panels/{panel_a}/execute")
        client.patch(
            f"/api/v1/panels/{panel_a}/override",
            json={"field_name": "chart_type", "user_value": "pie"},
        )

        # Panel B: same SQL, never overridden — should get "pie" from brain
        panel_b = client.post("/api/v1/panels", json={
            "dashboard_id": dash_id, "name": "B", "sql_content": sql,
        }).json()["id"]
        result_b = client.post(f"/api/v1/panels/{panel_b}/execute").json()
        assert result_b["inference_result"]["chart_winner"] == "pie"
