"""Dashboard aggregate lifecycle through the real authorized HTTP API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlviz_api.dependencies import get_dashboard_deletion
from sqlviz_api.services.dashboards import DashboardDeletionService
from sqlviz_storage.brain_db import get_brain_connection
from sqlviz_storage.dashboard_repository import dashboard_write


def setup(client: TestClient) -> dict[str, str]:
    ids: dict[str, str] = {}
    folder = client.post("/api/v1/folders", json={"name": "Keep"}).json()["id"]
    for key in ("a", "b"):
        ids[key] = client.post(
            "/api/v1/dashboards", json={"name": key, "folder_id": folder},
        ).json()["id"]
        ids["panel_" + key] = client.post("/api/v1/panels", json={
            "dashboard_id": ids[key], "name": key,
            "sql_content": "SELECT 'North' AS region, 10 AS revenue",
        }).json()["id"]
    ids["folder"] = folder
    return ids


def grant(client: TestClient, parent: str | None, mode: str = "password") -> dict:
    route = f"/api/v1/dashboards/{parent}/share" if parent else "/api/v1/workspace/share"
    response = client.post(route, json={"mode": mode, "password": "synthetic-password"})
    assert response.status_code == 201, response.text
    return response.json()


def unlock(viewer: TestClient, share: dict, *, workspace: bool = False) -> str:
    route = "/view/workspace/" if workspace else "/view/"
    response = viewer.post(route + share["token"] + "/unlock", json={
        "password": "synthetic-password",
    })
    assert response.status_code == 200, response.text
    return response.json()["viewer_session"]


def test_delete_cleans_owned_data_and_revokes_only_its_sessions(client: TestClient) -> None:
    ids = setup(client)
    app = client.app
    conn = app.state.db_conn
    for key in ("a", "b"):
        conn.execute("INSERT INTO filter_memory VALUES (?, 'region', 'North', 't')", [ids[key]])
    conn.execute("CREATE TABLE sales (amount INTEGER)")
    conn.execute("INSERT INTO sales VALUES (42)")
    conn.execute("INSERT INTO connections VALUES ('keep', 'keep', 'duckdb', '{}', 't')")
    conn.execute("INSERT INTO settings VALUES ('theme', 'dark', 't')")
    before_auth = conn.execute("SELECT * FROM _sqlviz_auth").fetchall()
    brain = get_brain_connection()  # The autouse fixture supplies an isolated DB.
    brain.execute("INSERT INTO feedback_events VALUES ('event', 'fp', 'chart_type', 'line', "
                  "'bar', ?, ?, 't')", [ids["panel_a"], ids["a"]])
    brain.execute("INSERT INTO feedback_patterns VALUES ('fp', 'chart_type', 'line', 'bar', 't')")
    before_brain = brain.execute("SELECT * FROM feedback_events").fetchall()
    owned = [grant(client, ids["a"], mode) for mode in ("public", "private", "password")]
    other, workspace = grant(client, ids["b"]), grant(client, None)
    with TestClient(app) as viewer:
        session_a = unlock(viewer, owned[-1])
        session_b = unlock(viewer, other)
        session_w = unlock(viewer, workspace, workspace=True)
        response = client.delete(f"/api/v1/dashboards/{ids['a']}")
        assert response.status_code == 204 and response.content == b""
        sessions = app.state.authorization.viewer_sessions
        assert not sessions.validate(session_a, owned[-1]["token"])
        assert sessions.validate(session_b, other["token"])
        assert sessions.validate(session_w, workspace["token"])
        for share in owned:
            assert viewer.get("/view/" + share["token"]).status_code == 404
            assert viewer.post("/view/" + share["token"] + "/unlock", json={
                "password": "synthetic-password",
            }).status_code == 404
        headers = {"X-SQLviz-Share": workspace["token"], "X-SQLviz-Viewer-Session": session_w}
        navigation = viewer.get("/view/workspace/" + workspace["token"], headers=headers)
        assert navigation.status_code == 200
        assert [d["id"] for d in navigation.json()["dashboards"]] == [ids["b"]]
        for reader, scope in ((client, {}), (viewer, headers)):
            panel_path = f"/api/v1/panels/{ids['panel_a']}"
            assert reader.get(panel_path, headers=scope).status_code == 404
            assert reader.post(panel_path + "/execute", headers=scope, json={}).status_code == 404
            assert reader.post(panel_path + "/filter-domain", headers=scope, json={
                "column": "region", "kind": "distinct",
            }).status_code == 404
        assert viewer.post(f"/api/v1/panels/{ids['panel_b']}/execute",
                           headers=headers, json={}).status_code == 200
    for table in ("panels", "shares", "filter_memory"):
        assert conn.execute(f"SELECT count(*) FROM {table} WHERE dashboard_id = ?",
                            [ids["a"]]).fetchone() == (0,)
        assert conn.execute(f"SELECT count(*) FROM {table} WHERE dashboard_id = ?",
                            [ids["b"]]).fetchone() == (1,)
    assert client.get(f"/api/v1/folders/{ids['folder']}").status_code == 200
    assert conn.execute("SELECT amount FROM sales").fetchone() == (42,)
    assert conn.execute("SELECT id FROM connections").fetchone() == ("keep",)
    assert conn.execute("SELECT value FROM settings").fetchone() == ("dark",)
    assert conn.execute("SELECT * FROM _sqlviz_auth").fetchall() == before_auth
    assert brain.execute("SELECT * FROM feedback_events").fetchall() == before_brain
    assert brain.execute("SELECT user_value FROM feedback_patterns").fetchone() == ("bar",)
    assert client.delete(f"/api/v1/dashboards/{ids['a']}").status_code == 404


def test_failed_delete_restores_rows_and_password_access(client: TestClient) -> None:
    ids = setup(client)
    conn = client.app.state.db_conn
    conn.execute("INSERT INTO filter_memory VALUES (?, 'region', 'North', 't')", [ids["a"]])
    conn.execute("CREATE TABLE retained (dashboard_id VARCHAR REFERENCES dashboards(id))")
    conn.execute("INSERT INTO retained VALUES (?)", [ids["a"]])
    share = grant(client, ids["a"])
    before = {table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
              for table in ("dashboards", "panels", "shares", "filter_memory")}
    with TestClient(client.app) as viewer:
        session = unlock(viewer, share)
        response = client.delete(f"/api/v1/dashboards/{ids['a']}")
        assert response.status_code == 409
        assert response.json()["code"] == "dashboard_write_conflict"
        assert share["token"] not in response.text and "retained" not in response.text
        assert client.app.state.authorization.viewer_sessions.validate(session, share["token"])
        headers = {"X-SQLviz-Share": share["token"], "X-SQLviz-Viewer-Session": session}
        assert viewer.get("/view/" + share["token"], headers=headers).status_code == 200
        assert viewer.post(f"/api/v1/panels/{ids['panel_a']}/execute",
                           headers=headers, json={}).status_code == 200
    assert {table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in before} == before
    conn.execute("DELETE FROM retained")
    assert client.delete(f"/api/v1/dashboards/{ids['a']}").status_code == 204


@pytest.mark.parametrize("operation", ["panel", "share", "delete"])
def test_competing_http_writes_return_conflict_then_retry_cleanly(client, operation) -> None:
    ids = setup(client)
    cursor = client.app.state.db_conn.cursor()

    def request():
        if operation == "panel":
            return client.post("/api/v1/panels", json={"dashboard_id": ids["a"], "name": "new"})
        if operation == "share":
            return client.post(f"/api/v1/dashboards/{ids['a']}/share", json={"mode": "public"})
        return client.delete(f"/api/v1/dashboards/{ids['a']}")

    try:
        with dashboard_write(cursor, ids["a"]):
            response = request()
            assert response.status_code == 409, response.text
            assert response.json()["code"] == "dashboard_write_conflict"
        assert request().status_code == (204 if operation == "delete" else 201)
    finally:
        cursor.close()


@pytest.mark.parametrize("operation", ["panel", "share"])
def test_child_creation_after_delete_returns_404_without_orphans(client, operation) -> None:
    ids = setup(client)
    assert client.delete(f"/api/v1/dashboards/{ids['a']}").status_code == 204
    if operation == "panel":
        response = client.post("/api/v1/panels", json={"dashboard_id": ids["a"], "name": "new"})
    else:
        response = client.post(f"/api/v1/dashboards/{ids['a']}/share", json={"mode": "public"})
    assert response.status_code == 404
    for table in ("panels", "shares"):
        assert client.app.state.db_conn.execute(
            f"SELECT count(*) FROM {table} WHERE dashboard_id = ?", [ids["a"]],
        ).fetchone() == (0,)


def test_unexpected_database_failure_does_not_revoke_viewer_access(client: TestClient) -> None:
    ids = setup(client)
    conn = client.app.state.db_conn
    share = grant(client, ids["a"])
    conn.execute("INSERT INTO filter_memory VALUES (?, 'region', 'North', 't')", [ids["a"]])
    conn.execute("ALTER TABLE filter_memory RENAME TO saved_filter_memory")
    conn.execute("CREATE VIEW filter_memory AS SELECT * FROM saved_filter_memory")
    before = {table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
              for table in ("dashboards", "panels", "shares", "filter_memory")}
    with TestClient(client.app, raise_server_exceptions=False) as caller, TestClient(
        client.app,
    ) as viewer:
        caller.cookies.update(client.cookies)
        session = unlock(viewer, share)
        response = caller.delete(f"/api/v1/dashboards/{ids['a']}")
        assert response.status_code == 500
        assert client.app.state.authorization.viewer_sessions.validate(session, share["token"])
        headers = {"X-SQLviz-Share": share["token"], "X-SQLviz-Viewer-Session": session}
        assert viewer.get("/view/" + share["token"], headers=headers).status_code == 200
    assert {table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in before} == before


def test_commit_failure_keeps_viewer_sessions(client: TestClient) -> None:
    # The storage adapter has already tested real rollback on commit failure.
    # This service-boundary failure proves that the router never revokes early.
    from unittest.mock import Mock

    from sqlviz_storage.dashboard_repository import DashboardWriteConflict

    ids = setup(client)
    share = grant(client, ids["a"])
    repository = Mock()
    repository.delete.side_effect = DashboardWriteConflict("synthetic commit conflict")
    service = DashboardDeletionService(repository, client.app.state.authorization.viewer_sessions)
    client.app.dependency_overrides[get_dashboard_deletion] = lambda: service
    try:
        with TestClient(client.app) as viewer:
            session = unlock(viewer, share)
            response = client.delete(f"/api/v1/dashboards/{ids['a']}")
            assert response.status_code == 409
            assert client.app.state.authorization.viewer_sessions.validate(session, share["token"])
            assert client.get(f"/api/v1/dashboards/{ids['a']}").status_code == 200
    finally:
        client.app.dependency_overrides.pop(get_dashboard_deletion)
