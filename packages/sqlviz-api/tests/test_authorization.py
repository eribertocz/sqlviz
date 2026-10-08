"""Author/viewer authorization matrix against the real API and in-memory database."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import duckdb
import pytest
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_api.services.access import SessionStore
from sqlviz_storage.project_db import create_project


@pytest.fixture
def workspace() -> Generator[
    tuple[TestClient, TestClient, duckdb.DuckDBPyConnection, dict[str, Any]], None, None
]:
    conn = create_project(":memory:")
    app = create_app(conn)
    with TestClient(app) as admin, TestClient(app) as viewer:
        admin.cookies.set("sqlviz_session", app.state.authorization.admin_sessions.issue())
        ids: dict[str, Any] = {}
        for key in ("a", "b"):
            dashboard = admin.post("/api/v1/dashboards", json={"name": key}).json()
            ids[key] = dashboard["id"]
            panel = admin.post(
                "/api/v1/panels",
                json={
                    "dashboard_id": ids[key],
                    "name": key,
                    "sql_content": "SELECT region, revenue FROM "
                    "(VALUES ('North', 10), ('South', 20)) sales(region, revenue) "
                    "WHERE region = $region",
                },
            ).json()
            ids["panel_" + key] = panel["id"]
        ids["folder"] = admin.post("/api/v1/folders", json={"name": "Folder"}).json()["id"]
        yield admin, viewer, conn, ids
    conn.close()


def share(admin: TestClient, dashboard_id: str | None, mode: str = "public") -> dict[str, Any]:
    path = f"/api/v1/dashboards/{dashboard_id}/share" if dashboard_id else "/api/v1/workspace/share"
    response = admin.post(path, json={"mode": mode, "password": "reader-password"})
    assert response.status_code == 201
    return response.json()


def headers(grant: dict[str, Any], session: str | None = None) -> dict[str, str]:
    result = {"X-SQLviz-Share": grant["token"]}
    if session:
        result["X-SQLviz-Viewer-Session"] = session
    return result


# Every project-data entrypoint must reject anonymous callers before doing work.
_AUTHOR_ROUTES = [
    ("GET", "/api/v1/dashboards", None),
    ("POST", "/api/v1/dashboards", {"name": "attack"}),
    ("GET", "/api/v1/dashboards/{a}", None),
    ("PATCH", "/api/v1/dashboards/{a}", {"name": "attack"}),
    ("DELETE", "/api/v1/dashboards/{a}", None),
    ("GET", "/api/v1/folders", None),
    ("POST", "/api/v1/folders", {"name": "attack"}),
    ("GET", "/api/v1/folders/{folder}", None),
    ("PATCH", "/api/v1/folders/{folder}", {"name": "attack"}),
    ("DELETE", "/api/v1/folders/{folder}", None),
    ("GET", "/api/v1/panels", None),
    ("GET", "/api/v1/panels/{panel_a}", None),
    ("POST", "/api/v1/panels", {"dashboard_id": "a", "sql_content": "SELECT 1"}),
    ("PATCH", "/api/v1/panels/{panel_a}", {"sql_content": "CREATE TABLE attack (x INT)"}),
    ("DELETE", "/api/v1/panels/{panel_a}", None),
    ("POST", "/api/v1/panels/{panel_a}/execute", {}),
    ("POST", "/api/v1/panels/{panel_a}/filter-domain", {"column": "region", "kind": "distinct"}),
    (
        "PATCH",
        "/api/v1/panels/{panel_a}/override",
        {"field_name": "chart_type", "user_value": "bar"},
    ),
    ("PATCH", "/api/v1/panels/{panel_a}/view-override", {"field": "title", "value": "attack"}),
    ("POST", "/api/v1/compose", []),
    ("POST", "/api/v1/dashboards/{a}/share", {"mode": "public"}),
    ("POST", "/api/v1/workspace/share", {"mode": "public"}),
    ("PATCH", "/api/v1/shares/unknown", {"revoked": True}),
    ("GET", "/api/v1/demo/dashboard", None),
    ("GET", "/api/v1/demo/sql", None),
]


@pytest.mark.parametrize("method,path,body", _AUTHOR_ROUTES)
def test_anonymous_project_routes_are_denied(workspace, method, path, body) -> None:
    admin, viewer, conn, ids = workspace
    before = conn.execute("SELECT * FROM panels ORDER BY id").fetchall()
    response = viewer.request(method, path.format(**ids), json=body)
    assert response.status_code == 401, response.text
    assert response.headers["cache-control"] == "no-store"
    assert conn.execute("SELECT * FROM panels ORDER BY id").fetchall() == before
    assert len(admin.get("/api/v1/dashboards").json()) == 2


def test_public_dashboard_grants_read_execute_domains_and_compose_only_in_scope(workspace) -> None:
    admin, viewer, _, ids = workspace
    grant = share(admin, ids["a"])
    access = headers(grant)
    assert viewer.get(f"/view/{grant['token']}").status_code == 200
    assert viewer.get(f"/api/v1/panels?dashboard_id={ids['a']}", headers=access).status_code == 200
    assert viewer.get(f"/api/v1/panels/{ids['panel_a']}", headers=access).status_code == 200
    result = viewer.post(f"/api/v1/panels/{ids['panel_a']}/execute", headers=access, json={})
    assert result.status_code == 200, result.text
    assert result.json()["data"] == [
        {"region": "North", "revenue": 10},
        {"region": "South", "revenue": 20},
    ]
    domain = viewer.post(
        f"/api/v1/panels/{ids['panel_a']}/filter-domain",
        headers=access,
        json={"column": "region", "kind": "distinct"},
    )
    assert domain.status_code == 200
    assert domain.json() == {"values": ["North", "South"]}
    compose = [{"panel_id": ids["panel_a"], "inference_result": result.json()["inference_result"]}]
    assert viewer.post("/api/v1/compose", headers=access, json=compose).status_code == 200
    assert viewer.post("/api/v1/compose", json=compose).status_code == 401
    assert viewer.get("/api/v1/panels", headers=access).status_code == 403


@pytest.mark.parametrize("operation", ["list", "get", "execute", "domain", "compose"])
def test_dashboard_grant_cannot_access_another_dashboard(workspace, operation) -> None:
    admin, viewer, _, ids = workspace
    access = headers(share(admin, ids["a"]))
    path = f"/api/v1/panels/{ids['panel_b']}"
    if operation == "list":
        response = viewer.get(f"/api/v1/panels?dashboard_id={ids['b']}", headers=access)
    elif operation == "get":
        response = viewer.get(path, headers=access)
    elif operation == "execute":
        response = viewer.post(path + "/execute", headers=access)
    elif operation == "domain":
        response = viewer.post(
            path + "/filter-domain", headers=access, json={"column": "region", "kind": "distinct"}
        )
    else:
        ir = admin.post(path + "/execute").json()["inference_result"]
        response = viewer.post(
            "/api/v1/compose",
            headers=access,
            json=[{"panel_id": ids["panel_b"], "inference_result": ir}],
        )
    assert response.status_code == 404


@pytest.mark.parametrize(
    "method,path,body",
    [
        r
        for r in _AUTHOR_ROUTES
        if r[0] in ("PATCH", "DELETE", "POST")
        and not r[1].endswith(("/execute", "/filter-domain", "/compose"))
    ],
)
def test_viewer_scope_rejects_mutations_even_with_admin_cookie(
    workspace, method, path, body
) -> None:
    admin, viewer, _, ids = workspace
    access = headers(share(admin, ids["a"]))
    for client in (viewer, admin):
        response = client.request(method, path.format(**ids), json=body, headers=access)
        assert response.status_code == 403, response.text


def test_workspace_grant_allows_both_dashboards_but_no_author_listing(workspace) -> None:
    admin, viewer, _, ids = workspace
    grant = share(admin, None)
    access = headers(grant)
    response = viewer.get(f"/view/workspace/{grant['token']}")
    assert response.status_code == 200
    assert len(response.json()["dashboards"]) == 2
    assert viewer.get("/api/v1/dashboards", headers=access).status_code == 403
    for key in ("a", "b"):
        assert (
            viewer.get(f"/api/v1/panels?dashboard_id={ids[key]}", headers=access).status_code == 200
        )
        assert (
            viewer.post(f"/api/v1/panels/{ids['panel_' + key]}/execute", headers=access).status_code
            == 200
        )


@pytest.mark.parametrize("workspace_scope", [False, True])
def test_password_unlock_issues_bound_session_and_revocation_invalidates_it(
    workspace, workspace_scope
) -> None:
    admin, viewer, _, ids = workspace
    grant = share(admin, None if workspace_scope else ids["a"], "password")
    path = f"/view/workspace/{grant['token']}" if workspace_scope else f"/view/{grant['token']}"
    panel_path = f"/api/v1/panels/{ids['panel_a']}/execute"
    assert viewer.get(path).json()["requires_password"] is True
    assert viewer.post(panel_path, headers=headers(grant)).status_code == 401
    assert viewer.post(path + "/unlock", json={"password": "wrong"}).status_code == 401
    unlocked = viewer.post(path + "/unlock", json={"password": "reader-password"})
    assert unlocked.status_code == 200
    access = headers(grant, unlocked.json()["viewer_session"])
    assert viewer.get(path, headers=access).status_code == 200
    assert viewer.post(panel_path, headers=access).status_code == 200
    admin.patch(f"/api/v1/shares/{grant['id']}", json={"revoked": True})
    assert viewer.post(panel_path, headers=access).status_code == 404
    assert viewer.get(path, headers=access).status_code == 404
    admin.patch(f"/api/v1/shares/{grant['id']}", json={"revoked": False})
    assert viewer.post(panel_path, headers=access).status_code == 401


def test_password_session_is_not_portable_to_another_share_or_application(workspace) -> None:
    admin, viewer, conn, ids = workspace
    first = share(admin, ids["a"], "password")
    second = share(admin, ids["b"], "password")
    session = viewer.post(
        f"/view/{first['token']}/unlock", json={"password": "reader-password"}
    ).json()["viewer_session"]
    assert (
        viewer.post(
            f"/api/v1/panels/{ids['panel_b']}/execute", headers=headers(second, session)
        ).status_code
        == 401
    )
    with TestClient(create_app(conn)) as other_app:
        assert (
            other_app.post(
                f"/api/v1/panels/{ids['panel_a']}/execute", headers=headers(first, session)
            ).status_code
            == 401
        )


def test_private_preview_requires_current_admin_session_but_remains_scoped(workspace) -> None:
    admin, viewer, _, ids = workspace
    grant = share(admin, ids["a"], "private")
    access = headers(grant)
    assert viewer.get(f"/view/{grant['token']}").status_code == 404
    assert (
        viewer.post(f"/api/v1/panels/{ids['panel_a']}/execute", headers=access).status_code == 404
    )
    assert admin.post(f"/api/v1/panels/{ids['panel_a']}/execute", headers=access).status_code == 200
    assert admin.post(f"/api/v1/panels/{ids['panel_b']}/execute", headers=access).status_code == 404
    admin.post("/api/v1/auth/logout")
    assert admin.post(f"/api/v1/panels/{ids['panel_a']}/execute", headers=access).status_code == 404


def test_reader_execution_does_not_persist_inference_or_learning(workspace) -> None:
    admin, viewer, conn, ids = workspace
    from sqlviz_storage.brain_db import get_brain_connection

    brain = get_brain_connection()
    # Sharing is an author write that now touches the aggregate timestamp.
    # Capture the baseline after it, then isolate the viewer's execution.
    access = headers(share(admin, ids["a"]))
    before_panels = conn.execute("SELECT * FROM panels ORDER BY id").fetchall()
    before_dashboards = conn.execute("SELECT * FROM dashboards ORDER BY id").fetchall()
    before_events = brain.execute("SELECT COUNT(*) FROM feedback_events").fetchone()
    assert (
        viewer.post(
            f"/api/v1/panels/{ids['panel_a']}/execute?debug=true", headers=access
        ).status_code
        == 200
    )
    assert conn.execute("SELECT * FROM panels ORDER BY id").fetchall() == before_panels
    assert conn.execute("SELECT * FROM dashboards ORDER BY id").fetchall() == before_dashboards
    assert brain.execute("SELECT COUNT(*) FROM feedback_events").fetchone() == before_events


def test_viewer_can_only_execute_saved_sql_with_bound_filter_values(workspace) -> None:
    admin, viewer, _, ids = workspace
    access = headers(share(admin, ids["a"]))
    response = viewer.post(
        f"/api/v1/panels/{ids['panel_a']}/execute", headers=access,
        json={"sql_content": "DELETE FROM dashboards", "variables": {"region": "North"}},
    )
    assert response.status_code == 422
    response = viewer.post(
        f"/api/v1/panels/{ids['panel_a']}/execute", headers=access,
        json={"variables": {"region": "North"}},
    )
    assert response.status_code == 200
    assert response.json()["data"] == [{"region": "North", "revenue": 10}]
    assert len(admin.get("/api/v1/dashboards").json()) == 2


@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE attack (x INT)",
        "DELETE FROM dashboards",
        "SELECT 1; CREATE TABLE attack (x INT)",
    ],
)
def test_viewer_rejects_stored_write_and_multistatement_sql(workspace, sql) -> None:
    admin, viewer, conn, ids = workspace
    admin.patch(f"/api/v1/panels/{ids['panel_a']}", json={"sql_content": sql})
    access = headers(share(admin, ids["a"]))
    assert (
        viewer.post(f"/api/v1/panels/{ids['panel_a']}/execute", headers=access).status_code == 403
    )
    assert len(admin.get("/api/v1/dashboards").json()) == 2
    assert (
        conn.execute("SELECT COUNT(*) FROM duckdb_tables() WHERE table_name = 'attack'").fetchone()[
            0
        ]
        == 0
    )


def test_secret_rotation_and_session_expiry_are_checked_on_data_requests(workspace) -> None:
    admin, viewer, _, ids = workspace
    now = [0.0]
    admin.app.state.authorization.viewer_sessions = SessionStore(lifetime=10, clock=lambda: now[0])
    grant = share(admin, ids["a"], "password")
    session = viewer.post(
        f"/view/{grant['token']}/unlock", json={"password": "reader-password"}
    ).json()["viewer_session"]
    access = headers(grant, session)
    now[0] = 11
    assert viewer.get(f"/api/v1/panels/{ids['panel_a']}", headers=access).status_code == 401
    session = viewer.post(
        f"/view/{grant['token']}/unlock", json={"password": "reader-password"}
    ).json()["viewer_session"]
    admin.post("/api/v1/auth/regenerate-secret")
    assert (
        viewer.post(
            f"/api/v1/panels/{ids['panel_a']}/execute", headers=headers(grant, session)
        ).status_code
        == 404
    )


def test_admin_cookie_cannot_be_replayed_in_another_app_or_after_logout(workspace) -> None:
    admin, _, conn, _ = workspace
    token = admin.cookies.get("sqlviz_session")
    with TestClient(create_app(conn)) as other:
        other.cookies.set("sqlviz_session", token)
        assert other.get("/api/v1/dashboards").status_code == 401
        other.post("/api/v1/auth/logout")
    assert admin.get("/api/v1/dashboards").status_code == 200
    admin.post("/api/v1/auth/logout")
    admin.cookies.set("sqlviz_session", token)
    assert admin.get("/api/v1/dashboards").status_code == 401
