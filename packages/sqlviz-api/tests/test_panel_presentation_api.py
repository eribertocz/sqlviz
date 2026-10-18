"""Presentation API contracts and rendering in author and scoped viewer."""

import json
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_api.dependencies import get_db
from sqlviz_storage.transactions import project_transaction


def seeded(client):
    dashboard = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    response = client.post("/api/v1/panels", json={
        "dashboard_id": dashboard, "name": "P",
        "sql_content": "SELECT 'A' AS category, 7 AS amount",
    })
    assert response.status_code == 201
    return response.json()


def snapshot(client):
    db = client.app.state.db_conn
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("panels", "dashboards", "_sqlviz_meta")}


@pytest.mark.parametrize("body", [
    {}, {"field": "title"}, {"value": "Revenue"}, {"field": "name", "value": "Other"},
    {"field": None, "value": "Other"}, {"field": 1, "value": "Other"},
    {"field": "title", "value": 1}, {"field": "title", "value": True},
    {"field": "title", "value": []}, {"field": "title", "value": " \n"},
    {"field": "title", "value": "x" * 513},
    {"field": "title", "value": "Other", "updated_at": "now"},
])
def test_invalid_request_never_writes_or_implicitly_clears(client, body):
    panel = seeded(client)
    db = client.app.state.db_conn
    db.execute("UPDATE panels SET view_title = 'Keep' WHERE id = ?", [panel["id"]])
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json=body)
    assert response.status_code == 422, response.text
    assert snapshot(client) == before
    assert all(set(error) == {"type", "loc", "msg"} for error in response.json()["detail"])


@pytest.mark.parametrize("field,column", [
    ("title", "view_title"), ("x_label", "view_x_label"), ("y_label", "view_y_label"),
])
@pytest.mark.parametrize("value", [None, "", "  Ventas · ñ  "])
def test_response_reports_the_confirmed_value_and_other_fields_are_preserved(
    client, field, column, value,
):
    panel = seeded(client)
    db = client.app.state.db_conn
    db.execute("UPDATE panels SET view_title = 'Keep', view_x_label = 'Year', "
               "view_y_label = 'Revenue' WHERE id = ?", [panel["id"]])
    before = client.get(f"/api/v1/panels/{panel['id']}").json()
    response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
        "field": field, "value": value,
    })
    assert response.status_code == 200
    normalized = value or None
    assert response.json() == {
        "status": "ok", "field": field, "value": normalized,
        "updated_at": response.json()["updated_at"],
    }
    assert client.get(f"/api/v1/panels/{panel['id']}").json() == {
        **before, column: normalized, "updated_at": response.json()["updated_at"],
    }


def test_invalid_unicode_does_not_reach_storage(client):
    panel = seeded(client)
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}/view-override",
                            content=json.dumps({"field": "title", "value": "\ud800"}),
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert snapshot(client) == before


def test_commit_failure_and_competing_write_return_stable_conflicts(client):
    panel = seeded(client)
    before = snapshot(client)

    def failing_cursor():
        cursor = client.app.state.db_conn.cursor()
        proxy = Mock(wraps=cursor)
        proxy.commit.side_effect = duckdb.TransactionException("synthetic private conflict")
        try:
            yield cast(duckdb.DuckDBPyConnection, proxy)
        finally:
            cursor.close()

    client.app.dependency_overrides[get_db] = failing_cursor
    try:
        response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
            "field": "title", "value": "After",
        })
        assert response.status_code == 409 and response.json()["code"] == "panel_write_conflict"
        assert "synthetic" not in response.text
    finally:
        client.app.dependency_overrides.clear()
    assert snapshot(client) == before
    writer = client.app.state.db_conn.cursor()
    try:
        with project_transaction(writer):
            writer.execute("UPDATE panels SET updated_at = 'held' WHERE id = ?", [panel["id"]])
            response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
                "field": "x_label", "value": "After",
            })
            assert response.status_code == 409
            assert snapshot(client) == before
        response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
            "field": "x_label", "value": "After",
        })
        assert response.status_code == 200
    finally:
        writer.close()


def test_openapi_requires_both_field_and_value(client):
    schema = client.get("/openapi.json").json()["components"]["schemas"]["PanelViewOverrideRequest"]
    assert set(schema["required"]) == {"field", "value"}
    assert schema["additionalProperties"] is False


def test_missing_panel_and_legacy_orphan_return_not_found(client):
    response = client.patch("/api/v1/panels/missing/view-override", json={
        "field": "title", "value": "After",
    })
    assert response.status_code == 404 and response.json()["code"] == "panel_not_found"
    panel = seeded(client)
    client.app.state.db_conn.execute("DELETE FROM dashboards WHERE id = ?", [panel["dashboard_id"]])
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
        "field": "title", "value": "After",
    })
    assert response.status_code == 404 and response.json()["code"] == "dashboard_not_found"
    assert snapshot(client) == before


@pytest.mark.parametrize("scope", ["dashboard", "workspace"])
def test_author_and_viewer_use_identical_presentation_and_reset_restores_defaults(client, scope):
    panel = seeded(client)
    path = f"/api/v1/panels/{panel['id']}/execute"
    original = client.post(path, json={"variables": {}}).json()["inference_result"]
    for field, value in (("title", "  Ventas · ñ  "), ("x_label", "Categoría"), ("y_label", "Bs")):
        response = client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
            "field": field, "value": value,
        })
        assert response.status_code == 200
    author = client.post(path, json={"variables": {}}).json()["inference_result"]
    assert author["title"] == "  Ventas · ñ  "
    assert author["visual_spec"]["x_label"] == "Categoría"
    assert author["visual_spec"]["y_label"] == "Bs"
    share_path = (f"/api/v1/dashboards/{panel['dashboard_id']}/share"
                  if scope == "dashboard" else "/api/v1/workspace/share")
    share = client.post(share_path, json={"mode": "public"})
    assert share.status_code == 201
    headers = {"X-SQLviz-Share": share.json()["token"]}
    admin_cookie = client.cookies.get("sqlviz_session")
    client.cookies.clear()
    try:
        response = client.post(path, json={"variables": {}}, headers=headers)
        assert response.status_code == 200, response.text
        viewer = response.json()["inference_result"]
        assert viewer["title"] == author["title"]
        assert viewer["visual_spec"]["x_label"] == author["visual_spec"]["x_label"]
        assert viewer["visual_spec"]["y_label"] == author["visual_spec"]["y_label"]
        assert client.patch(f"/api/v1/panels/{panel['id']}/view-override", headers=headers,
                            json={"field": "title", "value": "Attack"}).status_code == 403
    finally:
        client.cookies.set("sqlviz_session", admin_cookie)
    for field in ("title", "x_label", "y_label"):
        assert client.patch(f"/api/v1/panels/{panel['id']}/view-override", json={
            "field": field, "value": None,
        }).status_code == 200
    reset = client.post(path, json={"variables": {}}).json()["inference_result"]
    assert reset["title"] == original["title"]
    assert reset["visual_spec"]["x_label"] is None and reset["visual_spec"]["y_label"] is None
