"""Session lifecycle and resource access policy, independent of FastAPI."""

from __future__ import annotations

import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from typing import Any, Literal

import duckdb
from sqlviz_storage.auth import verify_password
from sqlviz_storage.sharing import get_session_secret, verify_share_token

WORKSPACE_ID = "__workspace__"
SESSION_LIFETIME_SECONDS = 24 * 60 * 60


class AccessDenied(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class Principal:
    role: Literal["admin", "viewer"]
    dashboard_id: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def require_dashboard(self, dashboard_id: str) -> None:
        if not self.is_admin and self.dashboard_id not in (WORKSPACE_ID, dashboard_id):
            raise AccessDenied(404, "Dashboard not found")


@dataclass
class _Session:
    last_seen_at: float
    binding: str | None


class SessionStore:
    """App-local, sliding sessions; a lock protects check/touch/revoke operations."""

    def __init__(
        self,
        *,
        lifetime: int = SESSION_LIFETIME_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._lifetime = lifetime
        self._clock = clock
        self._sessions: dict[str, _Session] = {}
        self._lock = Lock()

    def issue(self, binding: str | None = None) -> str:
        with self._lock:
            now = self._clock()
            self._sessions = {
                token: session
                for token, session in self._sessions.items()
                if now - session.last_seen_at <= self._lifetime
            }
            token = secrets.token_urlsafe(32)
            self._sessions[token] = _Session(now, binding)
            return token

    def validate(self, token: str | None, binding: str | None = None) -> bool:
        if not token:
            return False
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return False
            now = self._clock()
            if now - session.last_seen_at > self._lifetime:
                del self._sessions[token]
                return False
            if session.binding != binding:
                return False
            session.last_seen_at = now
            return True

    def revoke(self, token: str | None) -> None:
        with self._lock:
            if token:
                self._sessions.pop(token, None)

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def revoke_binding(self, binding: str) -> None:
        with self._lock:
            self._sessions = {
                token: session
                for token, session in self._sessions.items()
                if session.binding != binding
            }


class AuthorizationService:
    def __init__(self, *, demo_mode: bool = False) -> None:
        self.demo_mode = demo_mode
        self.admin_sessions = SessionStore()
        self.viewer_sessions = SessionStore()

    def is_admin(self, token: str | None) -> bool:
        return self.demo_mode or self.admin_sessions.validate(token)

    def require_admin(self, token: str | None, *, share_token: str | None = None) -> Principal:
        # An explicitly scoped request never inherits broader cookie/demo rights.
        if share_token is not None:
            raise AccessDenied(403, "Viewer access is read-only")
        if not self.is_admin(token):
            raise AccessDenied(401, "Not authenticated")
        return Principal("admin")

    def get_share(self, db: duckdb.DuckDBPyConnection, token: str) -> dict[str, Any]:
        row = db.execute(
            "SELECT id, dashboard_id, nonce, token, mode, password_hash, revoked "
            "FROM shares WHERE token = ?",
            [token],
        ).fetchone()
        if row is None:
            raise AccessDenied(404, "Share not found")
        share = dict(
            zip(("id", "dashboard_id", "nonce", "token", "mode", "password_hash", "revoked"), row)
        )
        if not verify_share_token(token, share, get_session_secret(db)):
            raise AccessDenied(404, "Share not found")
        if (
            share["dashboard_id"] != WORKSPACE_ID
            and db.execute(
                "SELECT id FROM dashboards WHERE id = ?", [share["dashboard_id"]]
            ).fetchone()
            is None
        ):
            raise AccessDenied(404, "Share not found")
        return share

    def require_share(
        self,
        db: duckdb.DuckDBPyConnection,
        token: str,
        *,
        admin_token: str | None = None,
        viewer_token: str | None = None,
    ) -> Principal:
        share = self.get_share(db, token)
        mode = share["mode"]
        if mode == "private":
            if not self.is_admin(admin_token):
                raise AccessDenied(404, "Share not found")
        elif mode == "password":
            if not self.viewer_sessions.validate(viewer_token, token):
                raise AccessDenied(401, "Share password required")
        elif mode != "public":
            raise AccessDenied(404, "Share not found")
        return Principal("viewer", str(share["dashboard_id"]))

    def unlock(
        self,
        db: duckdb.DuckDBPyConnection,
        token: str,
        password: str,
        *,
        workspace: bool,
    ) -> str:
        share = self.get_share(db, token)
        if (share["dashboard_id"] == WORKSPACE_ID) != workspace or share["mode"] != "password":
            raise AccessDenied(404, "Share not found")
        if not verify_password(password, str(share["password_hash"] or "")):
            raise AccessDenied(401, "Invalid password")
        return self.viewer_sessions.issue(token)

    @staticmethod
    def require_panel(db: duckdb.DuckDBPyConnection, principal: Principal, panel_id: str) -> None:
        row = db.execute(
            "SELECT p.dashboard_id FROM panels p JOIN dashboards d ON d.id = p.dashboard_id "
            "WHERE p.id = ?",
            [panel_id],
        ).fetchone()
        if row is None:
            raise AccessDenied(404, "Panel not found")
        principal.require_dashboard(str(row[0]))
