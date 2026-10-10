"""Strict HTTP patch semantics, rollback and editor-compatible draft saving."""

from __future__ import annotations

import json
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_api.dependencies import get_db
from sqlviz_storage.dashboard_repository import dashboard_write


def seeded(client):
    folder = client.post("/api/v1/folders", json={"name": "Group"}).json()["id"]
    dashboard = client.post("/api/v1/dashboards", json={
        "name": "Before", "description": "Keep", "folder_id": folder,
        "connection_id": "source-ref",
    }).json()
    response = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={
        "sql_content": "SELECT 1",
    })
    assert response.status_code == 200, response.text
    client.app.state.db_conn.execute(
        "UPDATE dashboards SET last_run_sql = 'SELECT 0', "
        "last_run_at = '2026-10-07T12:00:00Z' WHERE id = ?",
        [dashboard['id']],
    )
    return client.get(f"/api/v1/dashboards/{dashboard['id']}").json()


def snapshot(client):
    db = client.app.state.db_conn
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("dashboards", "folders", "_sqlviz_meta")}


@pytest.mark.parametrize("field", [
    "folder_id", "connection_id", "description",
])
def test_null_clears_only_the_supplied_nullable_field(client, field):
    before = seeded(client)
    response = client.patch(f"/api/v1/dashboards/{before['id']}", json={field: None})
    assert response.status_code == 200, response.text
    expected = {**before, field: None, "updated_at": response.json()["updated_at"]}
    assert response.json() == expected
    assert client.get(f"/api/v1/dashboards/{before['id']}").json() == expected


def test_empty_patch_is_a_read_without_timestamp_or_tree_revision_changes(client):
    before = seeded(client)
    rows = snapshot(client)
    response = client.patch(f"/api/v1/dashboards/{before['id']}", json={})
    assert response.status_code == 200 and response.json() == before
    assert snapshot(client) == rows
    assert client.patch("/api/v1/dashboards/missing", json={}).status_code == 404


@pytest.mark.parametrize("body", [
    {"name": None}, {"name": ""}, {"name": " \n"}, {"name": 4}, {"name": "x" * 257},
    {"sort_order": None}, {"sort_order": True}, {"sort_order": 1.0}, {"sort_order": "1"},
    {"sort_order": -(2**31) - 1}, {"sort_order": 2**31},
    {"sql_content": None}, {"sql_content": []}, {"last_run_sql": False},
    {"folder_id": 4}, {"connection_id": True}, {"description": []},
    {"description": "x" * 16_385}, {"connection_id": "x" * 257},
    {"last_run_at": "2026-10-07T12:00:00"}, {"last_run_at": "yesterday"},
    {"last_run_at": 1_234}, {"last_run_at": ""}, {"updated_at": "now"},
    {"dashboard_hint": "sales"},
])
def test_invalid_field_rejects_the_entire_patch_before_writing(client, body):
    dashboard = seeded(client)
    before = snapshot(client)
    response = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={
        "description": "Must not save", "folder_id": None, **body,
    })
    assert response.status_code == 422, response.text
    assert snapshot(client) == before


def test_invalid_unicode_does_not_reach_duckdb(client):
    dashboard = seeded(client)
    before = snapshot(client)
    response = client.patch(f"/api/v1/dashboards/{dashboard['id']}",
                            content=json.dumps({"name": "\ud800"}),
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert snapshot(client) == before


def test_draft_and_last_run_keep_exact_text_and_can_be_cleared_independently(client):
    dashboard = seeded(client)
    draft = "-- texto español\r\nSELECT 'a;b' AS text;\n\n"
    response = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={
        "sql_content": draft, "sort_order": 0,
    })
    assert response.status_code == 200 and response.json()["sql_content"] == draft
    assert response.json()["last_run_sql"] == "SELECT 0"
    cleared = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={"sql_content": ""})
    assert cleared.status_code == 200 and cleared.json()["sql_content"] == ""
    assert cleared.json()["last_run_sql"] == "SELECT 0"


@pytest.mark.parametrize("with_placement", [False, True])
def test_commit_failure_returns_conflict_and_rolls_back_all_fields(client, with_placement):
    dashboard = seeded(client)
    before = snapshot(client)

    def failing_cursor():
        cursor = client.app.state.db_conn.cursor()
        proxy = Mock(wraps=cursor)
        proxy.commit.side_effect = duckdb.TransactionException("synthetic commit conflict")
        try:
            yield cast(duckdb.DuckDBPyConnection, proxy)
        finally:
            cursor.close()

    client.app.dependency_overrides[get_db] = failing_cursor
    try:
        response = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={
            "name": "Must roll back", "description": None,
            **({"folder_id": None} if with_placement else {}),
        })
        assert response.status_code == 409
        assert response.json()["code"] == (
            "folder_write_conflict" if with_placement else "dashboard_write_conflict"
        )
        assert "synthetic" not in response.text
    finally:
        client.app.dependency_overrides.clear()
    assert snapshot(client) == before


def test_concurrent_write_conflict_preserves_fields_and_retry_succeeds(client):
    dashboard = seeded(client)
    before = snapshot(client)
    cursor = client.app.state.db_conn.cursor()
    try:
        with dashboard_write(cursor, dashboard["id"]):
            response = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={
                "name": "After", "description": None,
            })
            assert response.status_code == 409
            assert response.json()["code"] == "dashboard_write_conflict"
            assert snapshot(client) == before
        response = client.patch(f"/api/v1/dashboards/{dashboard['id']}", json={"name": "After"})
        assert response.status_code == 200 and response.json()["name"] == "After"
        assert response.json()["description"] == "Keep"
    finally:
        cursor.close()
