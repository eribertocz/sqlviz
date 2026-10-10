"""SQLviz API — FastAPI application factory.

Usage:
    conn = create_project("my_project.sqlviz")  # or open_project(...)
    app = create_app(conn)
    uvicorn.run(app, host="127.0.0.1", port=4000)

The DuckDB connection is stored in app.state.db_conn and injected into each
request via the get_db dependency (dependencies.py).

AuthorizationService in app.state.authorization owns app-local admin and viewer
sessions. Author routers require admin; panel reads/execution/composition validate
scope on every request. get_db closes each request's cursor. Analytical database
execution uses QueryService's separate catalog; metadata cursors never execute
user SQL. Legacy physical data tables are projected without attaching the project.
The legacy QuackConnectionRouter is retained in app.state for compatibility and
is not the authorization boundary or the HTTP transport used by viewers.

Frontend protection (FastAPI ≥ 0.139.0, DOC3 §8):
  router.frontend() is registered with dependencies=[Depends(require_admin)]
  so the dashboard is only accessible to authenticated sessions.

  Unauthenticated browser requests to non-API frontend paths are handled
  by a scoped exception handler:
    - /login   → serves index.html directly (login form must always render)
    - all other frontend paths → 302 redirect to /login

  API routes (/api/v1/*) and share-view routes (/view/*) always return JSON
  401; the exception handler never intercepts them.

  Demo mode bypasses all auth checks via require_admin's demo_mode guard, so
  sqlviz (no args) works without any login.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlviz_core.models.folders import FolderError
from sqlviz_core.models.parameters import ParameterError, ParameterLimits
from sqlviz_core.models.sql_reconciliation import SqlReconciliationError
from sqlviz_core.models.sql_script import SqlScriptError
from sqlviz_core.version import __version__
from sqlviz_storage.dashboard_repository import DashboardNotFound, DashboardWriteConflict
from sqlviz_storage.folder_repository import FolderWriteConflict
from sqlviz_storage.inference_publication import InferencePublicationConflict
from sqlviz_storage.panel_repository import PanelNotFound, PanelWriteConflict
from sqlviz_storage.sql_script_repository import (
    SqlDefinitionConflict,
    SqlScriptMetadataError,
    SqlScriptStateLimitError,
    SqlScriptWriteConflict,
)

from sqlviz_api.quack_server import QuackConnectionRouter
from sqlviz_api.request_limits import RequestBodyLimitMiddleware
from sqlviz_api.routers import (
    auth,
    compose,
    dashboards,
    demo,
    folders,
    meta,
    panels,
    shares,
    sql_script_commits,
    sql_scripts,
)
from sqlviz_api.routers.auth import require_admin
from sqlviz_api.services.access import AuthorizationService
from sqlviz_api.services.parameters import ParameterService
from sqlviz_api.services.queries import QueryFailure, QueryLimits, QueryService
from sqlviz_api.services.sql_scripts import SqlScriptService


def create_app(
    db_conn: duckdb.DuckDBPyConnection,
    *,
    viewer_conn: duckdb.DuckDBPyConnection | None = None,
    demo_mode: bool = False,
    query_limits: QueryLimits | None = None,
    parameter_limits: ParameterLimits | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        db_conn: Open read/write DuckDB connection to the active project.
                 Stored in app.state for metadata and trusted source snapshots.
        viewer_conn: Optional read-only DuckDB connection for viewer requests
                     (Phase 6). None in demo mode or when read-only isolation
                     is not needed.
        demo_mode: When True, all auth checks are bypassed — no password is
                   required. Used by `sqlviz` (no args) demo mode.
        query_limits: App-local analytical budgets. None uses bounded defaults.
        parameter_limits: App-local named-value budgets. None uses bounded defaults.

    Returns:
        Configured FastAPI application ready for uvicorn.
    """
    app = FastAPI(title="SQLviz API", version=__version__)

    app.state.db_conn = db_conn
    app.state.demo_mode = demo_mode
    app.state.authorization = AuthorizationService(demo_mode=demo_mode)
    app.state.queries = QueryService(query_limits, parameter_limits=parameter_limits)
    app.state.parameters = ParameterService(parameter_limits)
    app.state.sql_scripts = SqlScriptService()

    @app.exception_handler(SqlReconciliationError)
    async def _sql_identity_failure(request: Request, exc: SqlReconciliationError) -> JSONResponse:
        return JSONResponse(
            status_code=413 if exc.code == "sql_reconciliation_limit" else 422,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(SqlScriptWriteConflict)
    async def _sql_commit_conflict(request: Request, exc: SqlScriptWriteConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={
            "detail": "Dashboard changed or has a conflicting dependency. Refresh and retry.",
            "code": "sql_script_write_conflict",
        })

    @app.exception_handler(SqlScriptMetadataError)
    async def _sql_metadata_failure(request: Request, exc: SqlScriptMetadataError) -> JSONResponse:
        return JSONResponse(status_code=500, content={
            "detail": "Stored SQL associations are invalid. The project requires repair.",
            "code": "sql_script_metadata_invalid",
        })

    @app.exception_handler(SqlScriptStateLimitError)
    async def _sql_state_limit(request: Request, exc: SqlScriptStateLimitError) -> JSONResponse:
        return JSONResponse(status_code=413, content={
            "detail": "Project script state exceeds supported limits.",
            "code": "sql_script_state_limit",
        })

    @app.exception_handler(SqlScriptError)
    async def _sql_script_failure(request: Request, exc: SqlScriptError) -> JSONResponse:
        return JSONResponse(status_code=413 if exc.code == "sql_script_limit" else 422, content={
            "detail": exc.detail, "code": exc.code,
        })

    @app.exception_handler(FolderError)
    async def _folder_error(request: Request, exc: FolderError) -> JSONResponse:
        status = 404 if exc.code == "folder_not_found" else (
            409 if exc.code == "folder_hierarchy_invalid" else 422
        )
        return JSONResponse(status_code=status, content={"detail": exc.detail, "code": exc.code})

    @app.exception_handler(FolderWriteConflict)
    async def _folder_conflict(request: Request, exc: FolderWriteConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={
            "detail": "Folder hierarchy changed concurrently or has a conflicting dependency. "
                      "Refresh and retry.",
            "code": "folder_write_conflict",
        })

    @app.exception_handler(DashboardNotFound)
    async def _dashboard_missing(request: Request, exc: DashboardNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={
            "detail": "Dashboard not found", "code": "dashboard_not_found",
        })

    @app.exception_handler(DashboardWriteConflict)
    async def _dashboard_conflict(request: Request, exc: DashboardWriteConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={
            "detail": "Dashboard changed concurrently or has a conflicting dependency. "
                      "Refresh and retry.",
            "code": "dashboard_write_conflict",
        })
    @app.exception_handler(SqlDefinitionConflict)
    async def _definition_conflict(request: Request, exc: SqlDefinitionConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={
            "detail": "Dashboard definitions changed during Run. "
                      "Reload and review query associations.",
            "code": "sql_definition_conflict",
        })

    @app.exception_handler(InferencePublicationConflict)
    async def _inference_conflict(
        request: Request, exc: InferencePublicationConflict,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={
            "detail": "Panel SQL or chart choice changed during execution, or inference "
                      "publication conflicted. Refresh and retry.",
            "code": "inference_publication_conflict",
        })

    @app.exception_handler(PanelNotFound)
    async def _panel_missing(request: Request, exc: PanelNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={
            "detail": "Panel not found", "code": "panel_not_found",
        })

    @app.exception_handler(PanelWriteConflict)
    async def _panel_conflict(request: Request, exc: PanelWriteConflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={
            "detail": "Panel changed concurrently or has a conflicting dependency. "
                      "Refresh and retry.",
            "code": "panel_write_conflict",
        })
    app.add_middleware(RequestBodyLimitMiddleware)

    @app.exception_handler(ParameterError)
    async def _parameter_failure(request: Request, exc: ParameterError) -> JSONResponse:
        return JSONResponse(status_code=413 if exc.code == "parameter_limit" else 422, content={
            "detail": exc.detail, "code": exc.code, "variable": exc.variable,
        })

    @app.exception_handler(RequestValidationError)
    async def _invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": [
            {key: error[key] for key in ("type", "loc", "msg")}
            for error in exc.errors()
        ]})

    @app.exception_handler(QueryFailure)
    async def _query_failure(request: Request, exc: QueryFailure) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={
            "detail": exc.detail, "code": exc.code,
        })
    app.state.quack_router = QuackConnectionRouter(
        admin_conn=db_conn,
        sessions=app.state.authorization.admin_sessions,
        session_lifetime=auth.SESSION_LIFETIME_SECONDS,
        viewer_conn=viewer_conn,
    )

    app.include_router(auth.router)
    app.include_router(compose.router)
    app.include_router(dashboards.router, dependencies=[Depends(require_admin)])
    app.include_router(demo.router, dependencies=[Depends(require_admin)])
    app.include_router(folders.router, dependencies=[Depends(require_admin)])
    app.include_router(meta.router)
    app.include_router(panels.router)
    app.include_router(shares.router)
    app.include_router(sql_scripts.router, dependencies=[Depends(require_admin)])
    app.include_router(sql_script_commits.router, dependencies=[Depends(require_admin)])

    @app.middleware("http")
    async def _private_data_cache(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        if request.url.path.startswith(("/api/v1/", "/view/")):
            response.headers["Cache-Control"] = "no-store"
        return response

    # SvelteKit SPA — only mounted when the production build exists.
    # Phase 4: dist/ is absent (frontend built in Phase 5). The if-guard
    # prevents a startup crash while keeping the wiring ready for Phase 5.
    frontend_dist = Path(__file__).parent / "static" / "dist"
    if frontend_dist.exists():
        _index_html = str(frontend_dist / "index.html")

        # Public SPA shell for share links. A browser *navigating* to
        # /view/<token> is served the SvelteKit app (which then fetches the JSON
        # from the same path). A fetch()/XHR must fall through to the JSON share
        # endpoint — so we gate on the navigation signal, not just Accept:
        # `Sec-Fetch-Dest: document` is a real page load; `empty` is a fetch.
        # (Older browsers without Sec-Fetch fall back to the Accept sniff.)
        # This deliberately bypasses admin auth — the token is the credential —
        # and runs before routing so require_admin never sees the request.
        @app.middleware("http")
        async def _spa_shell_for_share_links(request: Request, call_next):  # type: ignore[no-untyped-def]
            if request.method == "GET" and request.url.path.startswith("/view/"):
                dest = request.headers.get("sec-fetch-dest", "")
                accept = request.headers.get("accept", "")
                is_navigation = dest == "document" or (
                    dest == "" and "text/html" in accept
                )
                if is_navigation:
                    # no-store so the browser never reuses this shell for the
                    # viewer's JSON fetch to the same /view/<token> URL.
                    return FileResponse(
                        _index_html, headers={"Cache-Control": "no-store"}
                    )
            return await call_next(request)

        protected = APIRouter(dependencies=[Depends(require_admin)])
        protected.frontend("/", directory=str(frontend_dist))
        app.include_router(protected)

        _dist_root = frontend_dist.resolve()

        # Convert frontend 401s to browser-friendly responses:
        #   /login                 → serve index.html so the login form renders
        #   an existing static file → serve it publicly (JS/CSS/fonts/images)
        #   any other page route    → 302 to /login
        # API (/api/*) and share-view (/view/*) routes are excluded — they keep
        # returning JSON 401 as the API contract requires.
        #
        # Serving static assets without auth is required: the whole frontend
        # (including the login page) lives behind require_admin, so the bundle's
        # /_app/*.js and /_app/*.css requests would otherwise 401 → redirect to
        # /login (HTML) → the browser receives HTML instead of JS → the SPA
        # never boots and /login renders blank. Assets are the same for every
        # user and carry no data, so serving them publicly is safe; the API
        # (which does carry data) stays protected.
        @app.exception_handler(HTTPException)
        async def _frontend_auth_redirect(
            request: Request, exc: HTTPException
        ) -> FileResponse | RedirectResponse | object:
            if exc.status_code == 401 and not request.url.path.startswith(
                ("/api/", "/view/")
            ):
                path = request.url.path
                if path.rstrip("/") == "/login":
                    return FileResponse(_index_html)
                # Serve a real static file publicly (path-traversal guarded).
                candidate = (frontend_dist / path.lstrip("/")).resolve()
                if _dist_root in candidate.parents and candidate.is_file():
                    return FileResponse(str(candidate))
                return RedirectResponse(url="/login", status_code=302)
            return await http_exception_handler(request, exc)

    return app
