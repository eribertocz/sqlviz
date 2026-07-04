"""Tests for POST /api/v1/auth/{login,logout,change-password} (DOC7 Section 3).

Session isolation: _sessions is module-level in routers/auth.py, so an
autouse fixture resets it before and after each test to prevent cross-test
contamination.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_api.routers.auth as auth_module
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage.auth import set_admin_password
from sqlviz_storage.project_db import create_project

_PASSWORD = "supersecret123"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_sessions() -> Generator[None, None, None]:
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


@pytest.fixture
def auth_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "test.sqlviz"))
    set_admin_password(conn, _PASSWORD)
    app = create_app(conn)
    with TestClient(app) as c:
        yield c
    conn.close()


def _login(client: TestClient, password: str = _PASSWORD) -> None:
    client.post("/api/v1/auth/login", json={"password": password})


# ── GET /me ───────────────────────────────────────────────────────────────────

class TestMe:

    def test_me_without_session_returns_401(self, auth_client: TestClient) -> None:
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_session_returns_200(self, auth_client: TestClient) -> None:
        _login(auth_client)
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 200

    def test_me_with_valid_session_returns_status_authenticated(
        self, auth_client: TestClient
    ) -> None:
        _login(auth_client)
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.json()["status"] == "authenticated"


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:

    def test_correct_password_returns_200(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/auth/login", json={"password": _PASSWORD})
        assert resp.status_code == 200

    def test_correct_password_sets_cookie(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/auth/login", json={"password": _PASSWORD})
        assert "sqlviz_session" in resp.cookies

    def test_correct_password_returns_status_ok(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/auth/login", json={"password": _PASSWORD})
        assert resp.json()["status"] == "ok"

    def test_wrong_password_returns_401(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/auth/login", json={"password": "wrong"})
        assert resp.status_code == 401

    def test_wrong_password_generic_message(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/auth/login", json={"password": "wrong"})
        assert resp.json()["detail"] == "Invalid password"

    def test_no_password_configured_returns_401(self, tmp_path: Path) -> None:
        # Empty password_hash → same generic 401 (anti-enumeration, DOC7 §3.2)
        conn = create_project(str(tmp_path / "nopw.sqlviz"))
        app = create_app(conn)
        with TestClient(app) as c:
            resp = c.post("/api/v1/auth/login", json={"password": "anything"})
        conn.close()
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid password"

    def test_no_password_configured_same_message_as_wrong(
        self, auth_client: TestClient, tmp_path: Path
    ) -> None:
        wrong_resp = auth_client.post("/api/v1/auth/login", json={"password": "nope"})
        conn = create_project(str(tmp_path / "nopw.sqlviz"))
        app = create_app(conn)
        with TestClient(app) as c:
            nopw_resp = c.post("/api/v1/auth/login", json={"password": "nope"})
        conn.close()
        assert wrong_resp.json()["detail"] == nopw_resp.json()["detail"]


# ── Logout ────────────────────────────────────────────────────────────────────

class TestLogout:

    def test_logout_returns_200(self, auth_client: TestClient) -> None:
        _login(auth_client)
        resp = auth_client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

    def test_logout_without_session_returns_200(self, auth_client: TestClient) -> None:
        resp = auth_client.post("/api/v1/auth/logout")
        assert resp.status_code == 200

    def test_logout_invalidates_session(self, auth_client: TestClient) -> None:
        _login(auth_client)
        auth_client.post("/api/v1/auth/logout")
        # Protected endpoint should now return 401
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        assert resp.status_code == 401

    def test_logout_clears_cookie(self, auth_client: TestClient) -> None:
        _login(auth_client)
        resp = auth_client.post("/api/v1/auth/logout")
        # Cookie should be cleared (empty or absent)
        cookie_val = resp.cookies.get("sqlviz_session", "")
        assert cookie_val == ""


# ── require_admin dependency ──────────────────────────────────────────────────

class TestRequireAdmin:

    def test_protected_endpoint_without_session_returns_401(
        self, auth_client: TestClient
    ) -> None:
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        assert resp.status_code == 401

    def test_protected_endpoint_with_valid_session_returns_200(
        self, auth_client: TestClient
    ) -> None:
        _login(auth_client)
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        assert resp.status_code == 200

    def test_protected_endpoint_not_authenticated_message(
        self, auth_client: TestClient
    ) -> None:
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        assert resp.json()["detail"] == "Not authenticated"


# ── Change password ───────────────────────────────────────────────────────────

class TestChangePassword:

    def test_wrong_current_password_returns_401(self, auth_client: TestClient) -> None:
        _login(auth_client)
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": "wrong",
            "new_password": "new123",
        })
        assert resp.status_code == 401

    def test_change_password_succeeds(self, auth_client: TestClient) -> None:
        _login(auth_client)
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        assert resp.status_code == 200

    def test_change_password_invalidates_current_session(
        self, auth_client: TestClient
    ) -> None:
        _login(auth_client)
        auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        # Subsequent protected call must be rejected — ALL sessions cleared
        resp = auth_client.post("/api/v1/auth/change-password", json={
            "current_password": "new123",
            "new_password": "another",
        })
        assert resp.status_code == 401

    def test_new_password_works_after_change(self, auth_client: TestClient) -> None:
        _login(auth_client)
        auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        resp = auth_client.post("/api/v1/auth/login", json={"password": "new123"})
        assert resp.status_code == 200

    def test_old_password_rejected_after_change(self, auth_client: TestClient) -> None:
        _login(auth_client)
        auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        resp = auth_client.post("/api/v1/auth/login", json={"password": _PASSWORD})
        assert resp.status_code == 401

    def test_change_password_invalidates_all_sessions(
        self, auth_client: TestClient
    ) -> None:
        # Log in twice to accumulate two session tokens
        _login(auth_client)
        _login(auth_client)
        import sqlviz_api.routers.auth as am
        assert len(am._sessions) >= 1

        # Change password — ALL sessions must be cleared
        auth_client.post("/api/v1/auth/change-password", json={
            "current_password": _PASSWORD,
            "new_password": "new123",
        })
        assert len(am._sessions) == 0
