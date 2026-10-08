"""Admin authentication — /api/v1/auth (DOC7 Section 3).

Sessions are in-memory (not persisted to .sqlviz). Restarting the process
invalidates all admin sessions — this is correct and expected for a local tool.

The app-local AuthorizationService owns sessions. HTTP access dependencies live
in security.py and protect author routes and scoped viewer operations.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from sqlviz_storage.auth import (
    get_stored_password_hash,
    set_admin_password,
    verify_password,
)
from sqlviz_storage.sharing import regenerate_session_secret

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import ChangePasswordRequest, LoginRequest
from sqlviz_api.security import AccessDep, AdminDep, is_admin, require_admin
from sqlviz_api.services.access import SESSION_LIFETIME_SECONDS

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

__all__ = ["AdminDep", "SESSION_LIFETIME_SECONDS", "is_admin", "require_admin", "router"]


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
def login(
    body: LoginRequest,
    db: DbDep,
    response: Response,
    request: Request,
    access: AccessDep,
) -> dict[str, str]:
    """POST /api/v1/auth/login — issue a session cookie on correct password.

    Returns generic 401 whether the password is wrong OR no password is
    configured — anti-enumeration principle (DOC7 §3.2).
    """
    stored_hash = get_stored_password_hash(db)
    if not verify_password(body.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    access.admin_sessions.revoke(request.cookies.get("sqlviz_session"))
    token = access.admin_sessions.issue()

    response.set_cookie(
        key="sqlviz_session",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=SESSION_LIFETIME_SECONDS,
        secure=request.url.scheme == "https",
    )
    return {"status": "ok"}


@router.post("/logout")
def logout(request: Request, response: Response, access: AccessDep) -> dict[str, str]:
    """POST /api/v1/auth/logout — invalidate the current session cookie."""
    token = request.cookies.get("sqlviz_session")
    access.admin_sessions.revoke(token)
    response.delete_cookie(key="sqlviz_session", httponly=True, samesite="strict")
    return {"status": "ok"}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: DbDep,
    _admin: AdminDep,
    access: AccessDep,
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
    access.admin_sessions.clear()
    return {"status": "ok"}


@router.post("/regenerate-secret")
def regenerate_secret(db: DbDep, _admin: AdminDep, access: AccessDep) -> dict[str, str]:
    """POST /api/v1/auth/regenerate-secret — rotate the session_secret.

    Invalidates ALL existing share links simultaneously (DOC7 §4.4).
    Every share token was derived from (dashboard_id, nonce, OLD_secret);
    verify_share_token() now computes against the NEW_secret and mismatches
    every previously-issued token without touching the shares rows themselves.
    """
    regenerate_session_secret(db)
    access.viewer_sessions.clear()
    return {"status": "ok"}
