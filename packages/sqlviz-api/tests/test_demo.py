"""Tests for GET /api/v1/demo/dashboard and GET /api/v1/demo/sql.

Verifies that the 4 demo queries produce exactly the expected chart types
(kpi, line, bar, bar_horizontal) via the full Dashboard Engine pipeline.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage.project_db import create_project


@pytest.fixture
def demo_client() -> Generator[TestClient, None, None]:
    conn = create_project(":memory:")
    app = create_app(conn, demo_mode=True)
    with TestClient(app) as c:
        yield c
    conn.close()


# ── /api/v1/demo/sql ─────────���────────────────────────────────────────────────

def test_demo_sql_returns_string(demo_client: TestClient) -> None:
    r = demo_client.get("/api/v1/demo/sql")
    assert r.status_code == 200
    body = r.json()
    assert "sql" in body
    assert isinstance(body["sql"], str)
    assert len(body["sql"]) > 0


def test_demo_sql_contains_four_statements(demo_client: TestClient) -> None:
    r = demo_client.get("/api/v1/demo/sql")
    sql = r.json()["sql"]
    # Semicolon-separated: 4 statements → 3 semicolons (trailing one omitted)
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    assert len(statements) == 4


# ── /api/v1/demo/dashboard — chart type assertions ───────────────────────────

def _panel_chart_types(demo_client: TestClient) -> list[str]:
    r = demo_client.get("/api/v1/demo/dashboard")
    assert r.status_code == 200
    layout = r.json()
    return [
        panel["inference_result"]["chart_winner"]
        for row in layout["rows"]
        for panel in row["panels"]
    ]


def test_demo_dashboard_has_four_panels(demo_client: TestClient) -> None:
    r = demo_client.get("/api/v1/demo/dashboard")
    assert r.status_code == 200
    layout = r.json()
    panels = [p for row in layout["rows"] for p in row["panels"]]
    assert len(panels) == 4


def test_demo_dashboard_chart_types(demo_client: TestClient) -> None:
    """All four V0.1 example chart types must be present."""
    chart_types = set(_panel_chart_types(demo_client))
    assert chart_types == {"kpi", "line", "bar", "bar_horizontal"}


def test_demo_dashboard_has_kpi(demo_client: TestClient) -> None:
    assert "kpi" in _panel_chart_types(demo_client)


def test_demo_dashboard_has_line(demo_client: TestClient) -> None:
    assert "line" in _panel_chart_types(demo_client)


def test_demo_dashboard_has_bar(demo_client: TestClient) -> None:
    assert "bar" in _panel_chart_types(demo_client)


def test_demo_dashboard_has_bar_horizontal(demo_client: TestClient) -> None:
    assert "bar_horizontal" in _panel_chart_types(demo_client)


def test_demo_dashboard_panels_have_data(demo_client: TestClient) -> None:
    """Every panel must carry non-empty result rows."""
    r = demo_client.get("/api/v1/demo/dashboard")
    layout = r.json()
    for row in layout["rows"]:
        for panel in row["panels"]:
            assert len(panel["data"]) > 0, (
                f"Panel {panel['panel_id']} has no data"
            )


def test_demo_dashboard_panels_have_layout(demo_client: TestClient) -> None:
    """Every panel must have col_span and row_index set."""
    r = demo_client.get("/api/v1/demo/dashboard")
    layout = r.json()
    for row in layout["rows"]:
        for panel in row["panels"]:
            assert panel["final_col_span"] > 0
            assert panel["row_index"] >= 0


# ── Demo mode regression: singleton-connection (DOC2 §5) ─────────────────────

def test_demo_mode_dashboard_accessible_without_session(
    demo_client: TestClient,
) -> None:
    """In demo mode all routes are open — no session cookie needed."""
    r = demo_client.get("/api/v1/demo/dashboard")
    assert r.status_code == 200


def test_demo_mode_me_returns_demo_true(demo_client: TestClient) -> None:
    """GET /auth/me in demo mode returns demo=True — used by frontend auto-seed."""
    r = demo_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["demo"] is True


def test_demo_mode_can_create_and_execute_panel(demo_client: TestClient) -> None:
    """Demo mode: full create→execute path works on the in-memory connection.

    This is the regression guard for the singleton-connection bug (DOC2 §5):
    demo mode uses a single :memory: connection shared across all requests.
    Creating a dashboard, creating a panel, and executing it must all succeed
    on that same connection without isolation errors.
    """
    dash = demo_client.post(
        "/api/v1/dashboards", json={"name": "Demo Test", "sort_order": 0}
    )
    assert dash.status_code == 201
    dash_id = dash.json()["id"]

    panel = demo_client.post(
        "/api/v1/panels",
        json={
            "dashboard_id": dash_id,
            "name": "Test Panel",
            "sql_content": "SELECT SUM(x) AS total FROM (VALUES (1.0),(2.0)) t(x)",
            "sort_order": 0,
        },
    )
    assert panel.status_code == 201
    panel_id = panel.json()["id"]

    exec_r = demo_client.post(f"/api/v1/panels/{panel_id}/execute")
    assert exec_r.status_code == 200
    body = exec_r.json()
    assert body["inference_result"]["chart_winner"] == "kpi"
    assert body["data"] == [{"total": 3.0}]
