"""HTTP adapters for application access policy."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request

from sqlviz_api.dependencies import DbDep
from sqlviz_api.services.access import AccessDenied, AuthorizationService, Principal


def access_service(request: Request) -> AuthorizationService:
    service: AuthorizationService = request.app.state.authorization
    return service


AccessDep = Annotated[AuthorizationService, Depends(access_service)]


def require_admin(request: Request, access: AccessDep) -> Principal:
    try:
        return access.require_admin(
            request.cookies.get("sqlviz_session"),
            share_token=request.headers.get("X-SQLviz-Share"),
        )
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


AdminDep = Annotated[Principal, Depends(require_admin)]


def is_admin(request: Request) -> bool:
    return access_service(request).is_admin(request.cookies.get("sqlviz_session"))


def require_reader(request: Request, db: DbDep, access: AccessDep) -> Principal:
    share_token = request.headers.get("X-SQLviz-Share")
    if share_token is None:
        return require_admin(request, access)
    try:
        return access.require_share(
            db,
            share_token,
            admin_token=request.cookies.get("sqlviz_session"),
            viewer_token=request.headers.get("X-SQLviz-Viewer-Session"),
        )
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


ReaderDep = Annotated[Principal, Depends(require_reader)]


def get_valid_share(request: Request, db: DbDep, token: str) -> dict[str, Any]:
    try:
        return access_service(request).get_share(db, token)
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


def require_share_access(request: Request, db: DbDep, token: str) -> Principal:
    try:
        return access_service(request).require_share(
            db,
            token,
            admin_token=request.cookies.get("sqlviz_session"),
            viewer_token=request.headers.get("X-SQLviz-Viewer-Session"),
        )
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


def unlock_viewer(
    request: Request, db: DbDep, token: str, password: str, *, workspace: bool
) -> str:
    try:
        return access_service(request).unlock(db, token, password, workspace=workspace)
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


def require_panel_access(db: DbDep, principal: Principal, panel_id: str) -> None:
    try:
        AuthorizationService.require_panel(db, principal, panel_id)
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None


def require_dashboard_access(principal: Principal, dashboard_id: str) -> None:
    try:
        principal.require_dashboard(dashboard_id)
    except AccessDenied as exc:
        raise HTTPException(exc.status_code, exc.detail) from None
