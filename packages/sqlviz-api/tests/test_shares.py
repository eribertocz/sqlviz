"""Tests for share-link endpoints (DOC7 Section 4).

Critical invariants tested:
  - Two shares for the SAME dashboard produce DIFFERENT tokens (nonce fix)
  - Revoking one share does not affect any other share of the same dashboard
  - Invalid / revoked tokens always return 404 (anti-enumeration)
  - regenerate-secret invalidates ALL shares simultaneously
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

_PASSWORD = "adminpass"


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
        "/api/v1/dashboards", json={"name": "Test Dashboard"}
    ).json()["id"])


# ── Create share ──────────────────────────────────────────────────────────────

class TestCreateShare:

    def test_create_private_share_returns_201(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        resp = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        )
        assert resp.status_code == 201

    def test_create_share_returns_token(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        data = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()
        assert "token" in data and len(data["token"]) == 24

    def test_invalid_mode_returns_422(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        resp = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "invalid"}
        )
        assert resp.status_code == 422

    def test_password_mode_requires_password_field(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        resp = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "password"}
        )
        assert resp.status_code == 422

    def test_nonexistent_dashboard_returns_404(
        self, admin_client: TestClient
    ) -> None:
        resp = admin_client.post(
            "/api/v1/dashboards/does-not-exist/share", json={"mode": "private"}
        )
        assert resp.status_code == 404

    def test_create_share_requires_admin(
        self, tmp_path: Path, dashboard_id: str, admin_client: TestClient
    ) -> None:
        # Log out, then try to create a share
        admin_client.post("/api/v1/auth/logout")
        resp = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        )
        assert resp.status_code == 401


# ── THE KEY INVARIANT: two shares, two tokens (nonce fix) ─────────────────────

class TestNonceUniqueness:

    def test_two_shares_same_dashboard_different_tokens(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        """Two shares for the SAME dashboard MUST produce two DIFFERENT tokens.

        This is the exact regression test for the pre-fix design bug described
        in DOC7 §4.1 and §8.1: without per-share nonces, the token was fully
        determined by (dashboard_id, session_secret) — meaning only ONE valid
        token could ever exist per dashboard, making "create a second share" a
        silent no-op that returned the same token.
        """
        tok1 = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        tok2 = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        assert tok1 != tok2

    def test_three_shares_all_different_tokens(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        tokens = [
            admin_client.post(
                f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
            ).json()["token"]
            for _ in range(3)
        ]
        assert len(set(tokens)) == 3


# ── Revocation isolation ──────────────────────────────────────────────────────

class TestRevocationIsolation:

    def test_revoke_one_share_leaves_other_intact(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        """Revoking one share must NOT affect any other share of the same dashboard.

        This is the other guarantee the nonce fix provides: before the fix,
        both shares would have had the SAME token, so revoking one effectively
        revoked both (since they were indistinguishable).
        """
        share1 = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()
        share2 = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()

        # Revoke only share1
        admin_client.patch(
            f"/api/v1/shares/{share1['id']}", json={"revoked": True}
        )

        # share1 token must now return 404
        assert admin_client.get(f"/view/{share1['token']}").status_code == 404

        # share2 token must still work
        assert admin_client.get(f"/view/{share2['token']}").status_code == 200

    def test_revoke_nonexistent_share_returns_404(
        self, admin_client: TestClient
    ) -> None:
        resp = admin_client.patch(
            "/api/v1/shares/does-not-exist", json={"revoked": True}
        )
        assert resp.status_code == 404

    def test_revoke_requires_admin(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        share_id = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["id"]
        admin_client.post("/api/v1/auth/logout")
        resp = admin_client.patch(f"/api/v1/shares/{share_id}", json={"revoked": True})
        assert resp.status_code == 401


# ── View: private mode ────────────────────────────────────────────────────────

class TestViewPrivate:

    def test_private_share_returns_200(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        resp = admin_client.get(f"/view/{token}")
        assert resp.status_code == 200

    def test_private_share_returns_dashboard_data(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        data = admin_client.get(f"/view/{token}").json()
        assert "dashboard" in data
        assert "panels" in data
        assert data["dashboard"]["id"] == dashboard_id

    def test_private_share_no_password_prompt(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        data = admin_client.get(f"/view/{token}").json()
        assert "requires_password" not in data

    def test_unknown_token_returns_404(self, admin_client: TestClient) -> None:
        resp = admin_client.get("/view/aaabbbcccdddeee111222333")
        assert resp.status_code == 404

    def test_revoked_private_share_returns_404(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        share = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()
        admin_client.patch(f"/api/v1/shares/{share['id']}", json={"revoked": True})
        assert admin_client.get(f"/view/{share['token']}").status_code == 404


# ── View: public mode ─────────────────────────────────────────────────────────

class TestViewPublic:

    def test_public_share_returns_200(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "public"}
        ).json()["token"]
        assert admin_client.get(f"/view/{token}").status_code == 200

    def test_public_share_returns_dashboard_data(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "public"}
        ).json()["token"]
        data = admin_client.get(f"/view/{token}").json()
        assert data["dashboard"]["id"] == dashboard_id


# ── View: password mode ───────────────────────────────────────────────────────

class TestViewPassword:

    _SHARE_PW = "sharepassword"

    def _make_password_share(
        self, client: TestClient, dashboard_id: str
    ) -> dict[str, str]:
        return client.post(  # type: ignore[return-value]
            f"/api/v1/dashboards/{dashboard_id}/share",
            json={"mode": "password", "password": self._SHARE_PW},
        ).json()

    def test_password_share_view_returns_requires_password(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = self._make_password_share(admin_client, dashboard_id)["token"]
        data = admin_client.get(f"/view/{token}").json()
        assert data.get("requires_password") is True

    def test_password_share_view_does_not_return_dashboard(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = self._make_password_share(admin_client, dashboard_id)["token"]
        data = admin_client.get(f"/view/{token}").json()
        assert "dashboard" not in data

    def test_unlock_correct_password_returns_200(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = self._make_password_share(admin_client, dashboard_id)["token"]
        resp = admin_client.post(
            f"/view/{token}/unlock", json={"password": self._SHARE_PW}
        )
        assert resp.status_code == 200

    def test_unlock_returns_dashboard_data(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = self._make_password_share(admin_client, dashboard_id)["token"]
        data = admin_client.post(
            f"/view/{token}/unlock", json={"password": self._SHARE_PW}
        ).json()
        assert data["dashboard"]["id"] == dashboard_id

    def test_unlock_wrong_password_returns_401(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = self._make_password_share(admin_client, dashboard_id)["token"]
        resp = admin_client.post(
            f"/view/{token}/unlock", json={"password": "wrong"}
        )
        assert resp.status_code == 401

    def test_unlock_private_share_returns_404(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        token = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        resp = admin_client.post(f"/view/{token}/unlock", json={"password": "x"})
        assert resp.status_code == 404


# ── regenerate-secret (DOC7 §4.4) ────────────────────────────────────────────

class TestRegenerateSecret:

    def test_regenerate_secret_returns_200(
        self, admin_client: TestClient
    ) -> None:
        resp = admin_client.post("/api/v1/auth/regenerate-secret")
        assert resp.status_code == 200

    def test_regenerate_secret_requires_admin(
        self, admin_client: TestClient
    ) -> None:
        admin_client.post("/api/v1/auth/logout")
        resp = admin_client.post("/api/v1/auth/regenerate-secret")
        assert resp.status_code == 401

    def test_regenerate_secret_invalidates_all_shares(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        """Rotating the secret must make ALL existing share links invalid at once."""
        tok1 = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]
        tok2 = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()["token"]

        # Both work before rotation
        assert admin_client.get(f"/view/{tok1}").status_code == 200
        assert admin_client.get(f"/view/{tok2}").status_code == 200

        admin_client.post("/api/v1/auth/regenerate-secret")

        # Both must fail after rotation
        assert admin_client.get(f"/view/{tok1}").status_code == 404
        assert admin_client.get(f"/view/{tok2}").status_code == 404

    def test_regenerate_secret_does_not_delete_share_rows(
        self, admin_client: TestClient, dashboard_id: str
    ) -> None:
        """Rows stay in the DB for audit history; only the token becomes invalid."""
        share = admin_client.post(
            f"/api/v1/dashboards/{dashboard_id}/share", json={"mode": "private"}
        ).json()

        admin_client.post("/api/v1/auth/regenerate-secret")

        # Row still exists (PATCH should find it)
        resp = admin_client.patch(
            f"/api/v1/shares/{share['id']}", json={"revoked": True}
        )
        assert resp.status_code == 200
