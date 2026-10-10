"""Execution may finish after an edit; obsolete inference must not be published."""

from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from fastapi.testclient import TestClient
from sqlviz_api.dependencies import get_db
from sqlviz_api.routers import panels as panels_router
from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.panel_repository import PanelRepository


def seeded(client, sql="SELECT 42 AS answer"):
    dashboard = client.post("/api/v1/dashboards", json={"name": "D"}).json()["id"]
    panel = client.post("/api/v1/panels", json={
        "dashboard_id": dashboard, "name": "P", "sql_content": sql,
    }).json()
    client.app.state.db_conn.execute(
        "UPDATE dashboards SET last_run_at = ?, last_run_sql = ? WHERE id = ?",
        ["2026-10-08T12:00:00+00:00", "previous source", dashboard],
    )
    return panel


def snapshot(client):
    with client.app.state.db_conn.cursor() as db:
        return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
                for table in ("dashboards", "panels", "dashboard_sql_scripts", "filter_memory")}


def after_query(client, monkeypatch, callback):
    original = client.app.state.queries.execute
    called = False

    def execute(*args, **kwargs):
        nonlocal called
        result = original(*args, **kwargs)
        if not called and not kwargs.get("schema_only"):
            called = True
            with client.app.state.db_conn.cursor() as competing:
                callback(competing)
        return result

    monkeypatch.setattr(client.app.state.queries, "execute", execute)


@pytest.mark.parametrize("change", ["sql", "delete_panel", "delete_dashboard", "chart"])
def test_inputs_changed_after_query_return_safe_conflict_without_publication(
    client, monkeypatch, change,
):
    panel = seeded(client)
    after_edit = None

    def mutate(db):
        nonlocal after_edit
        if change == "sql":
            PanelRepository(db).update(panel["id"], {"sql_content": "SELECT 99 AS private_value"})
        elif change == "delete_panel":
            PanelRepository(db).delete(panel["id"])
        elif change == "delete_dashboard":
            DashboardRepository(db).delete(panel["dashboard_id"])
        else:
            PanelRepository(db).set_override(panel["id"], "chart_type", "bar")
        after_edit = snapshot(client)

    after_query(client, monkeypatch, mutate)
    response = client.post(f"/api/v1/panels/{panel['id']}/execute")
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "inference_publication_conflict"
    assert "data" not in response.json()
    assert "SELECT" not in response.text and "private_value" not in response.text
    assert snapshot(client) == after_edit


def test_compatible_size_and_title_edits_are_preserved_and_used_in_the_response(
    client, monkeypatch,
):
    panel = seeded(client)

    def mutate(db):
        repository = PanelRepository(db)
        repository.set_override(panel["id"], "col_span", "6")
        repository.set_override(panel["id"], "height_px", "320")
        repository.set_presentation(panel["id"], "title", "New title · ñ")

    after_query(client, monkeypatch, mutate)
    response = client.post(f"/api/v1/panels/{panel['id']}/execute")
    assert response.status_code == 200, response.text
    result = response.json()["inference_result"]
    assert result["col_span"] == 6 and result["panel_height_px"] == 320
    assert result["title"] == "New title · ñ"
    assert response.json()["data"] == [{"answer": 42}]
    saved = client.get(f"/api/v1/panels/{panel['id']}").json()
    assert saved["selected_col_span"] == saved["col_span_user_override"] == 6
    assert saved["selected_height_px"] == saved["height_user_override"] == 320
    assert saved["view_title"] == "New title · ñ"
    assert saved["fingerprint"]
    parent = client.get(f"/api/v1/dashboards/{panel['dashboard_id']}").json()
    assert parent["last_run_sql"] == "previous source"
    assert parent["last_run_at"] == "2026-10-08T12:00:00+00:00"


def test_saved_source_is_guarded_not_the_rewritten_parameter_query(client):
    panel = seeded(client, "SELECT $value AS answer")
    response = client.post(
        f"/api/v1/panels/{panel['id']}/execute", json={"variables": {"value": 42}},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"] == [{"answer": 42}]
    saved = client.get(f"/api/v1/panels/{panel['id']}").json()
    assert saved["sql_content"] == "SELECT $value AS answer" and saved["fingerprint"]


def test_classifier_failure_remains_best_effort_and_inference_is_saved(client, monkeypatch):
    panel = seeded(client)

    def fail(*args):
        raise ValueError("synthetic classifier failure")

    monkeypatch.setattr(panels_router, "classify_dashboard", fail)
    response = client.post(f"/api/v1/panels/{panel['id']}/execute")
    assert response.status_code == 200, response.text
    assert client.get(f"/api/v1/panels/{panel['id']}").json()["fingerprint"]


@pytest.mark.parametrize("fault", ["commit", "classification_read", "classification_write"])
def test_storage_failure_cannot_be_hidden_as_success_or_leave_partial_inference(
    client, fault,
):
    panel = seeded(client)
    before = snapshot(client)

    def failing_cursor():
        with client.app.state.db_conn.cursor() as cursor:
            proxy = Mock(wraps=cursor)
            if fault == "commit":
                proxy.commit.side_effect = duckdb.TransactionException("private commit failure")
            else:
                def execute(sql, *args):
                    if (
                        fault == "classification_read"
                        and sql.startswith("SELECT inferred_intent_type")
                    ) or (
                        fault == "classification_write" and sql.startswith(
                            "UPDATE dashboards SET dashboard_hint",
                        )
                    ):
                        raise duckdb.TransactionException("private storage conflict")
                    return cursor.execute(sql, *args)

                proxy.execute.side_effect = execute
            yield cast(duckdb.DuckDBPyConnection, proxy)

    client.app.dependency_overrides[get_db] = failing_cursor
    try:
        response = client.post(f"/api/v1/panels/{panel['id']}/execute")
        assert response.status_code == 409, response.text
        assert response.json()["code"] == "inference_publication_conflict"
        assert "private" not in response.text
    finally:
        client.app.dependency_overrides.clear()
    assert snapshot(client) == before
    assert client.post(f"/api/v1/panels/{panel['id']}/execute").status_code == 200


def test_held_competing_edit_blocks_publication_and_retry_uses_new_definition(client):
    panel = seeded(client)
    before = snapshot(client)
    with client.app.state.db_conn.cursor() as editing:
        editing.begin()
        editing.execute(
            "UPDATE panels SET sql_content = 'SELECT 99 AS answer', updated_at = 'held' "
            "WHERE id = ?",
            [panel["id"]],
        )
        response = client.post(f"/api/v1/panels/{panel['id']}/execute")
        assert response.status_code == 409, response.text
        assert snapshot(client) == before
        editing.commit()
    response = client.post(f"/api/v1/panels/{panel['id']}/execute")
    assert response.status_code == 200 and response.json()["data"] == [{"answer": 99}]


def test_readers_execute_without_persisting_inference_or_classification(client, monkeypatch):
    panel = seeded(client)
    share = client.post(f"/api/v1/dashboards/{panel['dashboard_id']}/share", json={
        "mode": "public",
    }).json()
    before = snapshot(client)

    def forbidden(*args, **kwargs):
        raise AssertionError("Readers must never publish inference")

    monkeypatch.setattr(panels_router, "inference_publication", forbidden)
    with TestClient(client.app) as viewer:
        response = viewer.post(f"/api/v1/panels/{panel['id']}/execute", headers={
            "X-SQLviz-Share": share["token"],
        })
    assert response.status_code == 200, response.text
    assert response.json()["data"] == [{"answer": 42}]
    assert snapshot(client) == before


def test_anonymous_requests_are_denied_before_execution_or_publication(client, monkeypatch):
    panel = seeded(client)
    before = snapshot(client)

    def forbidden(*args, **kwargs):
        raise AssertionError("Anonymous request reached execution")

    monkeypatch.setattr(client.app.state.queries, "execute", forbidden)
    monkeypatch.setattr(panels_router, "inference_publication", forbidden)
    client.cookies.clear()
    response = client.post(f"/api/v1/panels/{panel['id']}/execute")
    assert response.status_code == 401 and snapshot(client) == before


@pytest.mark.parametrize("sql", ["THIS IS NOT SQL !!!", "SELECT $value AS answer"])
def test_nonexecuted_fallback_does_not_publish_metadata(client, sql):
    panel = seeded(client, sql)
    before = snapshot(client)
    response = client.post(f"/api/v1/panels/{panel['id']}/execute")
    assert response.status_code == 200 and response.json()["inference_result"]["fallback_applied"]
    assert snapshot(client) == before
