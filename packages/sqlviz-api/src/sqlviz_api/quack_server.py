"""Legacy connection selector retained for existing integration points.

HTTP routes use get_db and the app-local AuthorizationService, not this selector.
A supplied viewer cursor may still be writable; selecting a connection does not
provide authorization or analytical isolation. Quack's optional remote service
is configured separately by the CLI and is not the HTTP viewer transport.
"""

from __future__ import annotations

import duckdb
from fastapi import Request

from sqlviz_api.services.access import SessionStore


class QuackConnectionRouter:
    """Select between caller-supplied connections; no read-only guarantee."""

    def __init__(
        self,
        admin_conn: duckdb.DuckDBPyConnection,
        sessions: SessionStore,
        session_lifetime: int,
        viewer_conn: duckdb.DuckDBPyConnection | None = None,
    ) -> None:
        self._admin_conn = admin_conn
        self._viewer_conn = viewer_conn
        self._sessions = sessions  # application-owned session store
        self._session_lifetime = session_lifetime

    def is_admin(self, request: Request) -> bool:
        """True if the request carries a valid, non-expired admin session cookie."""
        token = request.cookies.get("sqlviz_session")
        if not token:
            return False
        return self._sessions.validate(token)

    def connection_for_request(self, request: Request) -> duckdb.DuckDBPyConnection:
        """Return the DuckDB connection appropriate for this request.

        Admin requests → read/write admin connection.
        Viewer requests → read-only viewer connection (Phase 6), or admin
        connection when running in demo mode (no viewer_conn available).
        """
        if self.is_admin(request):
            return self._admin_conn
        return self._viewer_conn if self._viewer_conn is not None else self._admin_conn
