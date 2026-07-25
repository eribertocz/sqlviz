"""Share-link endpoints (DOC7 Section 4).

Admin endpoints (require_admin):
  POST  /api/v1/dashboards/{id}/share  — create a share (private/password/public)
  PATCH /api/v1/shares/{share_id}      — revoke a specific share

Public endpoints (no auth — the token IS the credential):
  GET   /view/{token}                  — access a share; 404 for unknown/revoked
  POST  /view/{token}/unlock           — unlock a password-protected share

Key invariant: token lookup is ALWAYS "SELECT FROM shares WHERE token = ?"
first — never recomputed from dashboard_id blind (DOC7 §4.2 lookup flow).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlviz_storage.auth import hash_password, verify_password
from sqlviz_storage.sharing import (
    generate_share_nonce,
    generate_share_token,
    get_session_secret,
    verify_share_token,
)

from sqlviz_api.dependencies import DbDep
from sqlviz_api.models import (
    ShareCreate,
    ShareCreateResponse,
    ShareRevokeRequest,
    UnlockRequest,
)
from sqlviz_api.routers.auth import AdminDep, is_admin

router = APIRouter(tags=["shares"])

_VALID_MODES: frozenset[str] = frozenset({"private", "password", "public"})

# Reserved sentinel used as the shares.dashboard_id for a *workspace* share
# (access to every dashboard, with navigation). Real dashboards use UUIDs, so
# this never collides. It keeps workspace shares in the same table/flow — the
# token still derives from (dashboard_id, nonce, secret) and stays revocable.
_WORKSPACE_ID = "__workspace__"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fetch_share_by_token(db: DbDep, token: str) -> dict[str, Any]:
    """Look up a share row by token. Always queries the DB — never recomputes."""
    row = db.execute(
        "SELECT id, dashboard_id, nonce, token, mode, password_hash, created_at, revoked "
        "FROM shares WHERE token = ?",
        [token],
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Share not found")
    return {
        "id": row[0],
        "dashboard_id": row[1],
        "nonce": row[2],
        "token": row[3],
        "mode": row[4],
        "password_hash": row[5],
        "created_at": row[6],
        "revoked": row[7],
    }


def _dashboard_view_data(db: DbDep, dashboard_id: str) -> dict[str, Any]:
    """Return dashboard + panels for the viewer response."""
    d = db.execute(
        "SELECT id, name, folder_id, connection_id, sort_order, created_at, updated_at "
        "FROM dashboards WHERE id = ?",
        [dashboard_id],
    ).fetchone()
    if d is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    panels_rows = db.execute(
        "SELECT id, dashboard_id, name, sql_content, sort_order, created_at, updated_at "
        "FROM panels WHERE dashboard_id = ? ORDER BY sort_order, created_at",
        [dashboard_id],
    ).fetchall()

    return {
        "dashboard": {
            "id": d[0],
            "name": d[1],
            "folder_id": d[2],
            "connection_id": d[3],
            "sort_order": d[4],
            "created_at": d[5],
            "updated_at": d[6],
        },
        "panels": [
            {
                "id": r[0],
                "dashboard_id": r[1],
                "name": r[2],
                "sql_content": r[3],
                "sort_order": r[4],
                "created_at": r[5],
                "updated_at": r[6],
            }
            for r in panels_rows
        ],
    }


def _workspace_view_data(db: DbDep) -> dict[str, Any]:
    """Return every folder + dashboard for a workspace share's navigable sidebar.

    Panels are fetched lazily by the viewer per dashboard (public panels API),
    so this stays a lightweight metadata listing.
    """
    folder_rows = db.execute(
        "SELECT id, name, parent_id, sort_order FROM folders "
        "ORDER BY sort_order, created_at"
    ).fetchall()
    dash_rows = db.execute(
        "SELECT id, name, folder_id, sort_order, dashboard_hint, dashboard_domain, "
        "description FROM dashboards ORDER BY sort_order, created_at"
    ).fetchall()
    return {
        "folders": [
            {"id": r[0], "name": r[1], "parent_id": r[2], "sort_order": r[3]}
            for r in folder_rows
        ],
        "dashboards": [
            {
                "id": r[0],
                "name": r[1],
                "folder_id": r[2],
                "sort_order": r[3],
                "dashboard_hint": r[4],
                "dashboard_domain": r[5],
                "description": r[6],
            }
            for r in dash_rows
        ],
    }


# ── Admin: create share ───────────────────────────────────────────────────────

@router.post(
    "/api/v1/dashboards/{dashboard_id}/share",
    response_model=ShareCreateResponse,
    status_code=201,
)
def create_share(
    dashboard_id: str,
    body: ShareCreate,
    db: DbDep,
    _admin: AdminDep,
) -> ShareCreateResponse:
    if body.mode not in _VALID_MODES:
        raise HTTPException(status_code=422, detail=f"Invalid mode {body.mode!r}")
    if body.mode == "password" and not body.password:
        raise HTTPException(
            status_code=422, detail="password required when mode='password'"
        )

    if db.execute("SELECT id FROM dashboards WHERE id = ?", [dashboard_id]).fetchone() is None:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")

    session_secret = get_session_secret(db)
    nonce = generate_share_nonce()
    token = generate_share_token(dashboard_id, nonce, session_secret)

    pw_hash: str | None = None
    if body.mode == "password" and body.password:
        pw_hash = hash_password(body.password)

    share_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        "INSERT INTO shares "
        "(id, dashboard_id, nonce, token, mode, password_hash, created_at, revoked) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, false)",
        [share_id, dashboard_id, nonce, token, body.mode, pw_hash, now],
    )
    return ShareCreateResponse(
        id=share_id,
        dashboard_id=dashboard_id,
        token=token,
        mode=body.mode,
        created_at=now,
    )


# ── Admin: revoke share ───────────────────────────────────────────────────────

@router.patch("/api/v1/shares/{share_id}", status_code=200)
def revoke_share(
    share_id: str,
    body: ShareRevokeRequest,
    db: DbDep,
    _admin: AdminDep,
) -> dict[str, str]:
    if db.execute("SELECT id FROM shares WHERE id = ?", [share_id]).fetchone() is None:
        raise HTTPException(status_code=404, detail=f"Share '{share_id}' not found")
    db.execute("UPDATE shares SET revoked = ? WHERE id = ?", [body.revoked, share_id])
    return {"status": "ok"}


# ── Public: view share ────────────────────────────────────────────────────────

@router.get("/view/{token}")
def view_share(token: str, db: DbDep, request: Request) -> JSONResponse:
    """Access a share by token.

    Returns 404 for: unknown token, revoked share, rotated secret.
    Never 403 — anti-enumeration principle (DOC7 §4.2).

    mode="private" is an admin-only *preview* link — it only opens for the
    authenticated admin; anyone else gets 404 (so it's never exposed).
    """
    share = _fetch_share_by_token(db, token)
    secret = get_session_secret(db)

    if not verify_share_token(token, share, secret):
        raise HTTPException(status_code=404, detail="Share not found")

    # A workspace token is not valid on the single-dashboard endpoint.
    if str(share["dashboard_id"]) == _WORKSPACE_ID:
        raise HTTPException(status_code=404, detail="Share not found")

    mode = str(share["mode"])
    if mode == "private" and not is_admin(request):
        raise HTTPException(status_code=404, detail="Share not found")
    if mode == "password":
        return JSONResponse(content={"requires_password": True, "mode": "password"})

    return JSONResponse(content=_dashboard_view_data(db, str(share["dashboard_id"])))


# ── Public: unlock password-protected share ───────────────────────────────────

@router.post("/view/{token}/unlock")
def unlock_share(token: str, body: UnlockRequest, db: DbDep) -> JSONResponse:
    share = _fetch_share_by_token(db, token)
    secret = get_session_secret(db)

    if not verify_share_token(token, share, secret):
        raise HTTPException(status_code=404, detail="Share not found")

    if str(share["dashboard_id"]) == _WORKSPACE_ID:
        raise HTTPException(status_code=404, detail="Share not found")

    if str(share["mode"]) != "password":
        raise HTTPException(status_code=404, detail="Share not found")

    stored = share.get("password_hash")
    if not verify_password(body.password, str(stored) if stored is not None else ""):
        raise HTTPException(status_code=401, detail="Invalid password")

    return JSONResponse(content=_dashboard_view_data(db, str(share["dashboard_id"])))


# ── Admin: create workspace share ─────────────────────────────────────────────

@router.post(
    "/api/v1/workspace/share",
    response_model=ShareCreateResponse,
    status_code=201,
)
def create_workspace_share(
    body: ShareCreate,
    db: DbDep,
    _admin: AdminDep,
) -> ShareCreateResponse:
    """Create a workspace share — one token granting access to every dashboard
    with navigation. Stored like a normal share but keyed by the reserved
    _WORKSPACE_ID sentinel.
    """
    if body.mode not in _VALID_MODES:
        raise HTTPException(status_code=422, detail=f"Invalid mode {body.mode!r}")
    if body.mode == "password" and not body.password:
        raise HTTPException(
            status_code=422, detail="password required when mode='password'"
        )

    session_secret = get_session_secret(db)
    nonce = generate_share_nonce()
    token = generate_share_token(_WORKSPACE_ID, nonce, session_secret)

    pw_hash: str | None = None
    if body.mode == "password" and body.password:
        pw_hash = hash_password(body.password)

    share_id = str(uuid.uuid4())
    now = _now()
    db.execute(
        "INSERT INTO shares "
        "(id, dashboard_id, nonce, token, mode, password_hash, created_at, revoked) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, false)",
        [share_id, _WORKSPACE_ID, nonce, token, body.mode, pw_hash, now],
    )
    return ShareCreateResponse(
        id=share_id,
        dashboard_id=_WORKSPACE_ID,
        token=token,
        mode=body.mode,
        created_at=now,
    )


# ── Public: view / unlock workspace share ─────────────────────────────────────

def _verify_workspace(db: DbDep, token: str) -> dict[str, Any]:
    share = _fetch_share_by_token(db, token)
    secret = get_session_secret(db)
    if not verify_share_token(token, share, secret):
        raise HTTPException(status_code=404, detail="Share not found")
    if str(share["dashboard_id"]) != _WORKSPACE_ID:
        raise HTTPException(status_code=404, detail="Share not found")
    return share


@router.get("/view/workspace/{token}")
def view_workspace_share(token: str, db: DbDep, request: Request) -> JSONResponse:
    share = _verify_workspace(db, token)
    mode = str(share["mode"])
    if mode == "private" and not is_admin(request):
        raise HTTPException(status_code=404, detail="Share not found")
    if mode == "password":
        return JSONResponse(content={"requires_password": True, "mode": "password"})
    return JSONResponse(content=_workspace_view_data(db))


@router.post("/view/workspace/{token}/unlock")
def unlock_workspace_share(token: str, body: UnlockRequest, db: DbDep) -> JSONResponse:
    share = _verify_workspace(db, token)
    if str(share["mode"]) != "password":
        raise HTTPException(status_code=404, detail="Share not found")
    stored = share.get("password_hash")
    if not verify_password(body.password, str(stored) if stored is not None else ""):
        raise HTTPException(status_code=401, detail="Invalid password")
    return JSONResponse(content=_workspace_view_data(db))
