"""HTTP contract and execute/compose round trips for manual panel dimensions."""

from collections.abc import Iterator

import duckdb
import pytest
import sqlviz_api.routers.panels as panels_router
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage.project_db import create_project


@pytest.fixture
def setup() -> Iterator[tuple[TestClient, duckdb.DuckDBPyConnection, str]]:
    db = create_project(":memory:")
    app = create_app(db)
    with TestClient(app) as client:
        client.cookies.set("sqlviz_session", app.state.authorization.admin_sessions.issue())
        dashboard = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
        panel = client.post("/api/v1/panels", json={
            "dashboard_id": dashboard, "name": "P",
            "sql_content": "SELECT SUM(n) AS total FROM (VALUES (1), (2)) t(n)",
        }).json()["id"]
        yield client, db, panel
    db.close()


@pytest.mark.parametrize("payload", [
    {"field_name": "col_span", "user_value": v}
    for v in ["-7", "0", "13", "", "6.0", "+6", " 6", "６", 6, True, [], {}]
] + [
    {"field_name": "height_px", "user_value": v}
    for v in ["0", "119", "901", "NaN", "Infinity", "1e3", "9" * 5000]
] + [
    {"field_name": "col_span"},
    {"field_name": "col_span", "user_value": "6", "typo": True},
    {"field_name": "unknown", "user_value": None},
])
def test_invalid_request_has_no_side_effects(setup, monkeypatch, payload):
    client, db, panel = setup
    before = db.execute("SELECT * FROM panels").fetchall()
    monkeypatch.setattr(panels_router, "get_brain_connection",
                        lambda: pytest.fail("Invalid requests must not open brain"))
    response = client.patch(f"/api/v1/panels/{panel}/override", json=payload)
    assert response.status_code == 422
    assert db.execute("SELECT * FROM panels").fetchall() == before


@pytest.mark.parametrize("field,value,column", [
    ("col_span", "1", "col_span_user_override"),
    ("col_span", "12", "col_span_user_override"),
    ("height_px", "120", "height_user_override"),
    ("height_px", "900", "height_user_override"),
])
def test_boundary_survives_execute_and_compose(setup, field, value, column):
    client, db, panel = setup
    response = client.patch(f"/api/v1/panels/{panel}/override",
                            json={"field_name": field, "user_value": value})
    assert response.status_code == 200
    assert response.json()[column] == int(value)
    result = client.post(f"/api/v1/panels/{panel}/execute").json()["inference_result"]
    result_field = "col_span" if field == "col_span" else "panel_height_px"
    assert result[result_field] == int(value)
    response = client.post("/api/v1/compose", json=[{
        "panel_id": panel, "inference_result": result,
    }])
    assert response.status_code == 200
    composed = response.json()["rows"][0]["panels"][0]
    assert composed["inference_result"][result_field] == int(value)
    if field == "col_span":
        assert composed["final_col_span"] == int(value)


def test_reset_does_not_open_optional_learning(setup, monkeypatch):
    client, db, panel = setup
    db.execute("UPDATE panels SET inferred_col_span = 8, "
               "selected_col_span = 6, col_span_user_override = 6 WHERE id = ?", [panel])
    monkeypatch.setattr(panels_router, "get_brain_connection",
                        lambda: pytest.fail("Reset does not require brain"))
    response = client.patch(f"/api/v1/panels/{panel}/override",
                            json={"field_name": "col_span", "user_value": None})
    assert response.status_code == 200
    assert response.json()["selected_col_span"] == 8
    assert response.json()["col_span_user_override"] is None


def test_learning_unavailable_still_returns_confirmed_save(setup, monkeypatch):
    client, db, panel = setup
    db.execute("UPDATE panels SET fingerprint = 'shape' WHERE id = ?", [panel])

    def unavailable():
        raise OSError("private path")

    monkeypatch.setattr(panels_router, "get_brain_connection", unavailable)
    response = client.patch(f"/api/v1/panels/{panel}/override",
                            json={"field_name": "height_px", "user_value": "480"})
    assert response.status_code == 200
    assert response.json()["selected_height_px"] == 480


def test_conflicting_save_returns_409_without_changes_or_learning(setup, monkeypatch):
    client, db, panel = setup
    monkeypatch.setattr(panels_router, "get_brain_connection",
                        lambda: pytest.fail("No learning after rejected save"))
    before = db.execute("SELECT * FROM panels").fetchall()
    with db.cursor() as writer:
        writer.execute("BEGIN")
        writer.execute("UPDATE panels SET selected_col_span = 8 WHERE id = ?", [panel])
        response = client.patch(f"/api/v1/panels/{panel}/override",
                                json={"field_name": "col_span", "user_value": "6"})
        assert response.status_code == 409
        writer.execute("ROLLBACK")
    assert db.execute("SELECT * FROM panels").fetchall() == before


def test_legacy_invalid_sizes_do_not_reach_renderer_or_pin_kpi(setup):
    client, db, panel = setup
    db.execute("UPDATE panels SET col_span_user_override = -7, "
               "height_user_override = 0 WHERE id = ?", [panel])
    result = client.post(f"/api/v1/panels/{panel}/execute").json()["inference_result"]
    assert 1 <= result["col_span"] <= 12
    assert 120 <= result["panel_height_px"] <= 900
    composed = client.post("/api/v1/compose", json=[{
        "panel_id": panel, "inference_result": result,
    }]).json()["rows"][0]["panels"][0]
    assert composed["final_col_span"] == 4
    assert db.execute("SELECT col_span_user_override, height_user_override "
                      "FROM panels WHERE id = ?", [panel]).fetchone() == (-7, 0)
