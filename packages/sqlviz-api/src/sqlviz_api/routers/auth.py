"""Admin authentication — /api/v1/auth (DOC7 Section 3).

Sessions are in-memory (not persisted to .sqlviz). Restarting the process
invalidates all admin sessions — this is correct and expected for a local tool.

require_admin is a FastAPI dependency that can be applied to any route that
requires an active admin session. As of Phase 4.3 it is NOT yet applied to
dashboards/panels/folders — that gate is a future delivery once the frontend
login flow is wired end-to-end (Phase 4.4+). Any route that does require it
should declare `_admin: AdminDep` as a parameter.
"""

from __future__ import annotations

import secrets
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlviz_storage.auth import (
    get_stored_password_hash,
    set_admin_password,
    verify_password,
)
from sqlviz_storage.sharing import regenerate_session_secret

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import ChangePasswordRequest, LoginRequest

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# In-memory session store — {token: {created_at, last_seen_at}} (DOC7 §3.3)
_sessions: dict[str, dict[str, float]] = {}

SESSION_LIFETIME_SECONDS: int = 24 * 60 * 60  # 24 hours, sliding window


def require_admin(request: Request) -> None:
    """FastAPI dependency — raises 401 if no valid admin session is present.

    In demo mode (app.state.demo_mode = True) all requests are allowed through
    without a session — the demo instance has no persistent data to protect.
    """
    if getattr(request.app.state, "demo_mode", False):
        return

    token = request.cookies.get("sqlviz_session")
    session = _sessions.get(token) if token else None

    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    now = time.time()
    if now - session["last_seen_at"] > SESSION_LIFETIME_SECONDS:
        del _sessions[token]  # type: ignore[arg-type]
        raise HTTPException(status_code=401, detail="Session expired")

    session["last_seen_at"] = now  # sliding window


AdminDep = Annotated[None, Depends(require_admin)]


@router.get("/me")
def me(request: Request, _admin: AdminDep) -> dict[str, str | bool]:
    """GET /api/v1/auth/me — 200 with valid session, 401 without.

    In demo mode returns {"status": "authenticated", "demo": True} so
    the frontend can activate Edit mode automatically (no SQL on first load).
    In normal mode returns {"status": "authenticated", "demo": False}.
    """
    demo: bool = getattr(request.app.state, "demo_mode", False)
    return {"status": "authenticated", "demo": demo}


@router.post("/login")
def login(body: LoginRequest, db: DbDep, response: Response) -> dict[str, str]:
    """POST /api/v1/auth/login — issue a session cookie on correct password.

    Returns generic 401 whether the password is wrong OR no password is
    configured — anti-enumeration principle (DOC7 §3.2).
    """
    stored_hash = get_stored_password_hash(db)
    if not verify_password(body.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = secrets.token_urlsafe(32)
    now = time.time()
    _sessions[token] = {"created_at": now, "last_seen_at": now}

    response.set_cookie(
        key="sqlviz_session",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=SESSION_LIFETIME_SECONDS,
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    """POST /api/v1/auth/logout — invalidate the current session cookie."""
    token = request.cookies.get("sqlviz_session")
    if token and token in _sessions:
        del _sessions[token]
    response.delete_cookie(key="sqlviz_session", httponly=True, samesite="strict")
    return {"status": "ok"}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: DbDep,
    _admin: AdminDep,
) -> dict[str, str]:
    """POST /api/v1/auth/change-password — requires active session + current password.

    Re-verifies current password even with a valid session (DOC7 §3.4):
    protects against a session left open on a shared machine being used to
    lock out the real admin.

    Invalidates ALL sessions (including the one that just changed the password)
    — re-login with the new password is required.
    """
    stored_hash = get_stored_password_hash(db)
    if not verify_password(body.current_password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    set_admin_password(db, body.new_password)
    _sessions.clear()
    return {"status": "ok"}


@router.post("/regenerate-secret")
def regenerate_secret(db: DbDep, _admin: AdminDep) -> dict[str, str]:
    """POST /api/v1/auth/regenerate-secret — rotate the session_secret.

    Invalidates ALL existing share links simultaneously (DOC7 §4.4).
    Every share token was derived from (dashboard_id, nonce, OLD_secret);
    verify_share_token() now computes against the NEW_secret and mismatches
    every previously-issued token without touching the shares rows themselves.
    """
    regenerate_session_secret(db)
    return {"status": "ok"}
