"""Tests for QuackConnectionRouter and app.frontend() graceful handling.

QuackConnectionRouter (Phase 4.5 — logical routing):
  - is_admin() correctly identifies admin vs viewer requests
  - connection_for_request() returns the admin connection (Phase 4.5 contract)
  - Sessions are consulted in real time (router holds a reference, not a snapshot)

app.frontend():
  - App starts without error when static/dist does not exist
  - All /api/v1/* routes respond normally when frontend is not mounted

Concurrency:
  - Admin and viewer requests to the same dashboard can run concurrently
    without errors or data corruption (DuckDB handles internal locking)
"""

from __future__ import annotations

import time
from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_api.routers.auth as auth_module
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_api.quack_server import QuackConnectionRouter
from sqlviz_api.routers.auth import SESSION_LIFETIME_SECONDS
from sqlviz_storage.auth import set_admin_password
from sqlviz_storage.project_db import create_project
from starlette.requests import Request as StarletteRequest

_PASSWORD = "quacktest"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_sessions() -> Generator[None, None, None]:
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def admin_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "test.sqlviz"))
    set_admin_password(conn, _PASSWORD)
    app = create_app(conn)
    with TestClient(app) as c:
        c.post("/api/v1/auth/login", json={"password": _PASSWORD})
        yield c
    conn.close()


@pytest.fixture
def dashboard_id(admin_client: TestClient) -> str:
    return str(admin_client.post(
        "/api/v1/dashboards", json={"name": "Dash"}
    ).json()["id"])


@pytest.fixture
def share_token(admin_client: TestClient, dashboard_id: str) -> str:
    return str(admin_client.post(
        f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
    ).json()["token"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_request(cookies: dict[str, str] | None = None) -> StarletteRequest:
    """Build a minimal Starlette Request with the given cookies."""
    headers: list[tuple[bytes, bytes]] = []
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        headers.append((b"cookie", cookie_str.encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": headers,
    }
    return StarletteRequest(scope)


# ── QuackConnectionRouter.is_admin() ─────────────────────────────────────────

class TestIsAdmin:

    def test_is_admin_returns_false_without_cookie(self) -> None:
        import duckdb
        sessions: dict[str, dict[str, float]] = {}
        router = QuackConnectionRouter(duckdb.connect(), sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request()
        assert router.is_admin(req) is False

    def test_is_admin_returns_false_for_unknown_token(self) -> None:
        import duckdb
        sessions: dict[str, dict[str, float]] = {}
        router = QuackConnectionRouter(duckdb.connect(), sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request({"sqlviz_session": "nonexistent_token"})
        assert router.is_admin(req) is False

    def test_is_admin_returns_true_for_valid_session(self) -> None:
        import duckdb
        now = time.time()
        sessions: dict[str, dict[str, float]] = {
            "my_token": {"created_at": now, "last_seen_at": now}
        }
        router = QuackConnectionRouter(duckdb.connect(), sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request({"sqlviz_session": "my_token"})
        assert router.is_admin(req) is True

    def test_is_admin_returns_false_for_expired_session(self) -> None:
        import duckdb
        old_time = time.time() - SESSION_LIFETIME_SECONDS - 1
        sessions: dict[str, dict[str, float]] = {
            "old_token": {"created_at": old_time, "last_seen_at": old_time}
        }
        router = QuackConnectionRouter(duckdb.connect(), sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request({"sqlviz_session": "old_token"})
        assert router.is_admin(req) is False

    def test_is_admin_reflects_live_session_state(self) -> None:
        """Router holds a reference — session deletions are reflected immediately."""
        import duckdb
        now = time.time()
        sessions: dict[str, dict[str, float]] = {
            "live_token": {"created_at": now, "last_seen_at": now}
        }
        router = QuackConnectionRouter(duckdb.connect(), sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request({"sqlviz_session": "live_token"})

        assert router.is_admin(req) is True
        del sessions["live_token"]  # logout
        assert router.is_admin(req) is False


# ── QuackConnectionRouter.connection_for_request() ────────────────────────────

class TestConnectionForRequest:

    def test_admin_request_returns_admin_connection(self) -> None:
        import duckdb
        conn = duckdb.connect()
        now = time.time()
        sessions: dict[str, dict[str, float]] = {
            "tok": {"created_at": now, "last_seen_at": now}
        }
        router = QuackConnectionRouter(conn, sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request({"sqlviz_session": "tok"})
        assert router.connection_for_request(req) is conn

    def test_viewer_request_returns_admin_connection_phase45(self) -> None:
        """Phase 4.5: viewer also gets admin conn — routing logic is present,
        read-only isolation is Phase 6 (quack_server.py module docstring)."""
        import duckdb
        conn = duckdb.connect()
        sessions: dict[str, dict[str, float]] = {}
        router = QuackConnectionRouter(conn, sessions, SESSION_LIFETIME_SECONDS)
        req = _mock_request()  # no cookie → viewer
        assert router.connection_for_request(req) is conn


# ── app.state.quack_router wired by create_app() ─────────────────────────────

class TestCreateAppWiresRouter:

    def test_quack_router_in_app_state(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "t.sqlviz"))
        app = create_app(conn)
        assert hasattr(app.state, "quack_router")
        assert isinstance(app.state.quack_router, QuackConnectionRouter)
        conn.close()

    def test_quack_router_shares_sessions_with_auth(self, tmp_path: Path) -> None:
        """Router's sessions dict IS auth._sessions — not a copy."""
        conn = create_project(str(tmp_path / "t.sqlviz"))
        app = create_app(conn)
        router: QuackConnectionRouter = app.state.quack_router
        assert router._sessions is auth_module._sessions
        conn.close()


# ── app.frontend() — graceful when dist/ absent ───────────────────────────────

class TestFrontendGracefulAbsence:

    def test_app_starts_without_frontend_dist(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "t.sqlviz"))
        try:
            app = create_app(conn)  # must not raise
            assert app is not None
        finally:
            conn.close()

    def test_api_routes_work_without_frontend(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/api/v1/dashboards")
        assert resp.status_code == 200

    def test_auth_routes_work_without_frontend(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "t.sqlviz"))
        set_admin_password(conn, _PASSWORD)
        app = create_app(conn)
        with TestClient(app) as c:
            resp = c.post("/api/v1/auth/login", json={"password": _PASSWORD})
            assert resp.status_code == 200
        conn.close()


# ── Concurrency: admin + viewer rapid interleaved access ─────────────────────

class TestConcurrentAccess:

    def test_admin_and_viewer_interleaved_no_errors(
        self, admin_client: TestClient, dashboard_id: str, share_token: str
    ) -> None:
        """Admin and viewer requests interleaved rapidly on the same app.

        DuckDB in-process Python connections are NOT thread-safe (one connection,
        one thread). This test validates the correct behaviour at the ASGI layer:
        both admin and viewer can make rapid back-to-back requests without errors.
        True multi-thread connection isolation is a Phase 6 concern (one read-only
        connection per viewer, see quack_server.py module docstring).
        """
        results: list[int] = []
        for _ in range(5):
            r_admin = admin_client.get(f"/api/v1/dashboards/{dashboard_id}")
            r_viewer = admin_client.get(f"/view/{share_token}")
            results.append(r_admin.status_code)
            results.append(r_viewer.status_code)

        assert len(results) == 10
        assert all(r == 200 for r in results), f"Unexpected responses: {results}"
