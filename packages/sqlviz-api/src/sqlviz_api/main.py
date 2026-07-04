"""SQLviz API — FastAPI application factory.

Usage:
    conn = create_project("my_project.sqlviz")  # or open_project(...)
    app = create_app(conn)
    uvicorn.run(app, host="127.0.0.1", port=4000)

The DuckDB connection is stored in app.state.db_conn and injected into each
request via the get_db dependency (dependencies.py).

The QuackConnectionRouter (quack_server.py) is stored in app.state.quack_router
and provides is_admin(request) / connection_for_request(request). In Phase 4.5
all requests use the same read/write connection; Phase 6 wires in read-only
viewer connections (see quack_server.py module docstring).

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
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from sqlviz_api.quack_server import QuackConnectionRouter
from sqlviz_api.routers import auth, compose, dashboards, demo, folders, panels, shares
from sqlviz_api.routers.auth import require_admin


def create_app(
    db_conn: duckdb.DuckDBPyConnection,
    *,
    viewer_conn: duckdb.DuckDBPyConnection | None = None,
    demo_mode: bool = False,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        db_conn: Open read/write DuckDB connection to the active project.
                 Stored in app.state and used for all admin requests.
        viewer_conn: Optional read-only DuckDB connection for viewer requests
                     (Phase 6). None in demo mode or when read-only isolation
                     is not needed.
        demo_mode: When True, all auth checks are bypassed — no password is
                   required. Used by `sqlviz` (no args) demo mode.

    Returns:
        Configured FastAPI application ready for uvicorn.
    """
    app = FastAPI(title="SQLviz API", version="0.1.0")

    app.state.db_conn = db_conn
    app.state.demo_mode = demo_mode
    app.state.quack_router = QuackConnectionRouter(
        admin_conn=db_conn,
        sessions=auth._sessions,
        session_lifetime=auth.SESSION_LIFETIME_SECONDS,
        viewer_conn=viewer_conn,
    )

    app.include_router(auth.router)
    app.include_router(compose.router)
    app.include_router(dashboards.router)
    app.include_router(demo.router)
    app.include_router(folders.router)
    app.include_router(panels.router)
    app.include_router(shares.router)

    # SvelteKit SPA — only mounted when the production build exists.
    # Phase 4: dist/ is absent (frontend built in Phase 5). The if-guard
    # prevents a startup crash while keeping the wiring ready for Phase 5.
    frontend_dist = Path(__file__).parent / "static" / "dist"
    if frontend_dist.exists():
        _index_html = str(frontend_dist / "index.html")

        protected = APIRouter(dependencies=[Depends(require_admin)])
        protected.frontend("/", directory=str(frontend_dist))
        app.include_router(protected)

        # Convert frontend 401s to browser-friendly responses:
        #   /login → serve index.html so the login form always renders
        #   everything else → 302 to /login
        # API (/api/*) and share-view (/view/*) routes are excluded — they
        # keep returning JSON 401 as the API contract requires.
        @app.exception_handler(HTTPException)
        async def _frontend_auth_redirect(
            request: Request, exc: HTTPException
        ) -> FileResponse | RedirectResponse | object:
            if exc.status_code == 401 and not request.url.path.startswith(
                ("/api/", "/view/")
            ):
                if request.url.path.rstrip("/") == "/login":
                    return FileResponse(_index_html)
                return RedirectResponse(url="/login", status_code=302)
            return await http_exception_handler(request, exc)

    return app
