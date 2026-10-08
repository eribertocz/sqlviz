"""Basic PATCH contracts, editor compatibility and transactional HTTP failures."""

import json
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_api.dependencies import get_db
from sqlviz_storage.panel_repository import PanelRepository
from sqlviz_storage.transactions import project_transaction


def seeded(client):
    dashboard = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    response = client.post("/api/v1/panels", json={
        "dashboard_id": dashboard, "name": "Before", "sql_content": "SELECT 1", "sort_order": 2,
    })
    assert response.status_code == 201
    return response.json()


def snapshot(client):
    db = client.app.state.db_conn
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("dashboards", "panels", "_sqlviz_meta")}


@pytest.mark.parametrize("body", [
    {"name": None}, {"name": ""}, {"name": " \n"}, {"name": 42}, {"name": "x" * 257},
    {"sql_content": None}, {"sql_content": []}, {"sql_content": False},
    {"sort_order": None}, {"sort_order": True}, {"sort_order": 1.0}, {"sort_order": "1"},
    {"sort_order": -(2**31) - 1}, {"sort_order": 2**31},
    {"dashboard_id": "other"}, {"id": "other"}, {"updated_at": "now"},
    {"selected_col_span": 6}, {"view_title": "Other"},
])
def test_invalid_fields_reject_the_whole_patch_without_partial_writes(client, body):
    panel = seeded(client)
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}", json={
        "name": "Must not save", "sql_content": "SELECT 2", **body,
    })
    assert response.status_code == 422, response.text
    assert snapshot(client) == before
    assert all(set(error) == {"type", "loc", "msg"} for error in response.json()["detail"])
    assert "Must not save" not in response.text


def test_invalid_unicode_returns_validation_error_before_reaching_duckdb(client):
    panel = seeded(client)
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}",
                            content=json.dumps({"sql_content": "\ud800"}),
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert snapshot(client) == before


def test_empty_patch_is_a_read_and_missing_panel_has_a_stable_error(client):
    panel = seeded(client)
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}", json={})
    assert response.status_code == 200 and response.json() == panel
    assert snapshot(client) == before
    response = client.patch("/api/v1/panels/missing", json={})
    assert response.status_code == 404 and response.json()["code"] == "panel_not_found"


def test_editor_request_keeps_exact_sql_zero_order_and_visual_settings(client):
    panel = seeded(client)
    db = client.app.state.db_conn
    db.execute("UPDATE panels SET chart_user_override = 'bar', selected_chart_type = 'bar', "
               "selected_col_span = 6, col_span_user_override = 6, selected_height_px = 300, "
               "height_user_override = 300, view_title = 'Keep' WHERE id = ?", [panel["id"]])
    before = client.get(f"/api/v1/panels/{panel['id']}").json()
    sql = "-- ñ\r\nSELECT 'a;b' AS label;\n"
    response = client.patch(f"/api/v1/panels/{panel['id']}", json={
        "sql_content": sql, "sort_order": 0,
    })
    expected = {**before, "sql_content": sql, "sort_order": 0,
                "updated_at": response.json()["updated_at"]}
    assert response.status_code == 200 and response.json() == expected
    assert client.get(f"/api/v1/panels/{panel['id']}").json() == expected
    assert client.get(f"/api/v1/panels?dashboard_id={panel['dashboard_id']}").json() == [expected]
    assert db.execute("SELECT view_title FROM panels WHERE id = ?", [panel["id"]]).fetchone() == (
        "Keep",
    )
    response = client.patch(f"/api/v1/panels/{panel['id']}", json={"sql_content": ""})
    assert response.status_code == 200 and response.json()["sql_content"] == ""
    assert response.json()["chart_user_override"] == "bar"


def test_patch_then_execution_remains_compatible_with_the_editor(client):
    panel = seeded(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}", json={
        "sql_content": "SELECT 'a;b' AS label, 7 AS amount", "sort_order": 0,
    })
    assert response.status_code == 200
    response = client.post(f"/api/v1/panels/{panel['id']}/execute", json={"variables": {}})
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_commit_failure_returns_conflict_and_restores_all_rows(client, method):
    panel = seeded(client)
    before = snapshot(client)

    def failing_cursor():
        cursor = client.app.state.db_conn.cursor()
        proxy = Mock(wraps=cursor)
        proxy.commit.side_effect = duckdb.TransactionException("synthetic private failure")
        try:
            yield cast(duckdb.DuckDBPyConnection, proxy)
        finally:
            cursor.close()

    client.app.dependency_overrides[get_db] = failing_cursor
    try:
        if method == "patch":
            response = client.patch(f"/api/v1/panels/{panel['id']}", json={
                "name": "Must roll back", "sql_content": "", "sort_order": -1,
            })
        else:
            response = client.delete(f"/api/v1/panels/{panel['id']}")
        assert response.status_code == 409 and response.json()["code"] == "panel_write_conflict"
        assert "synthetic" not in response.text and "private" not in response.text
    finally:
        client.app.dependency_overrides.clear()
    assert snapshot(client) == before


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_competing_panel_write_returns_conflict_and_retry_succeeds(client, method):
    panel = seeded(client)
    writer = client.app.state.db_conn.cursor()
    before = snapshot(client)
    try:
        with project_transaction(writer):
            writer.execute("UPDATE panels SET updated_at = 'held' WHERE id = ?", [panel["id"]])
            if method == "patch":
                response = client.patch(f"/api/v1/panels/{panel['id']}", json={"name": "After"})
            else:
                response = client.delete(f"/api/v1/panels/{panel['id']}")
            assert response.status_code == 409
            assert response.json()["code"] == "panel_write_conflict"
            assert snapshot(client) == before
        if method == "patch":
            response = client.patch(f"/api/v1/panels/{panel['id']}", json={"name": "After"})
            assert response.status_code == 200 and response.json()["name"] == "After"
        else:
            assert client.delete(f"/api/v1/panels/{panel['id']}").status_code == 204
    finally:
        writer.close()


def test_legacy_orphan_is_not_updated(client):
    panel = seeded(client)
    client.app.state.db_conn.execute("DELETE FROM dashboards WHERE id = ?", [panel["dashboard_id"]])
    before = snapshot(client)
    response = client.patch(f"/api/v1/panels/{panel['id']}", json={"name": "After"})
    assert response.status_code == 404 and response.json()["code"] == "dashboard_not_found"
    assert snapshot(client) == before
    # Deletion can still clean up an already orphaned legacy row.
    assert client.delete(f"/api/v1/panels/{panel['id']}").status_code == 204


def test_dashboard_deletion_is_rejected_while_a_panel_patch_is_uncommitted(client):
    panel = seeded(client)
    before = snapshot(client)
    writer = client.app.state.db_conn.cursor()
    proxy = Mock(wraps=writer)

    def commit():
        response = client.delete(f"/api/v1/dashboards/{panel['dashboard_id']}")
        assert response.status_code == 409
        assert response.json()["code"] == "dashboard_write_conflict"
        assert snapshot(client) == before
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
            panel["id"], {"name": "After"},
        )
        assert client.get(f"/api/v1/panels/{panel['id']}").json()["name"] == "After"
        assert client.delete(f"/api/v1/dashboards/{panel['dashboard_id']}").status_code == 204
    finally:
        writer.close()
