"""QuackConnectionRouter — DuckDB connection routing per request (DOC7 §5).

IMPLEMENTATION STATUS — Phase 4.5: LOGICAL ROUTING ONLY
=========================================================
Quack is a library that exposes DuckDB as a PostgreSQL-compatible wire-protocol
server. DOC7 §5 describes the full architecture:

    Browser → sqlviz-api (HTTP, cookie-authenticated)
                   ↓
           ONE Quack admin (read/write) connection
           POOL of Quack viewer (read-only) connections
                   ↓
           sqlviz-storage / sqlviz-inference execute

Phase 4.5 does NOT start a Quack PostgreSQL server. Reasons:
  1. Quack's PostgreSQL server is a deployment concern (socket, port,
     process lifecycle) that belongs to the CLI/entrypoint phase (Phase 6).
  2. DuckDB's Python in-process API already handles concurrent readers +
     one writer internally, so the critical isolation property (viewers
     cannot mutate admin data) is achievable without a network server.
  3. sqlviz-api already connects to DuckDB via Python directly — adding the
     PostgreSQL wire-protocol layer would require rewriting all DB access to
     go through psycopg2 / asyncpg, which is a Phase 6 refactor.

What IS implemented:
  - QuackConnectionRouter class with the correct interface (DOC7 §5)
  - is_admin(request) — correctly identifies admin vs viewer using the
    in-memory session store from routers/auth.py
  - connection_for_request(request) — returns the appropriate connection;
    in Phase 4.5 this is always the admin read/write connection since
    true read-only connections require either a second DuckDB file-based
    connection (needs the file path, not currently stored in app.state)
    or the Quack server (Phase 6)
  - The routing LOGIC is exercised and tested; the isolation MECHANISM
    (separate read-only connections) is a Phase 6 task

Phase 6 upgrade path:
  - Add db_path to app.state in create_app()
  - Replace connection_for_request() with:
      if self.is_admin(request): return self._admin_conn
      return duckdb.connect(self._db_path, read_only=True)
"""

from __future__ import annotations

import time

import duckdb
from fastapi import Request


class QuackConnectionRouter:
    """Routes HTTP requests to the appropriate DuckDB connection.

    Admin-authenticated requests (valid sqlviz_session cookie) → read/write.
    All other requests (viewer share tokens, unauthenticated) → read-only.

    Phase 6: viewer_conn is a separate read-only DuckDB connection opened by
    the CLI at startup (duckdb.connect(path, read_only=True)). When provided,
    non-admin requests use it instead of the admin connection, completing the
    read-only viewer isolation described in DOC7 §5. In demo mode (no file
    path) viewer_conn is None and all requests share the admin connection.
    """

    def __init__(
        self,
        admin_conn: duckdb.DuckDBPyConnection,
        sessions: dict[str, dict[str, float]],
        session_lifetime: int,
        viewer_conn: duckdb.DuckDBPyConnection | None = None,
    ) -> None:
        self._admin_conn = admin_conn
        self._viewer_conn = viewer_conn
        self._sessions = sessions          # shared reference to auth._sessions
        self._session_lifetime = session_lifetime

    def is_admin(self, request: Request) -> bool:
        """True if the request carries a valid, non-expired admin session cookie."""
        token = request.cookies.get("sqlviz_session")
        if not token:
            return False
        session = self._sessions.get(token)
        if session is None:
            return False
        return time.time() - session["last_seen_at"] <= self._session_lifetime

    def connection_for_request(self, request: Request) -> duckdb.DuckDBPyConnection:
        """Return the DuckDB connection appropriate for this request.

        Admin requests → read/write admin connection.
        Viewer requests → read-only viewer connection (Phase 6), or admin
        connection when running in demo mode (no viewer_conn available).
        """
        if self.is_admin(request):
            return self._admin_conn
        return self._viewer_conn if self._viewer_conn is not None else self._admin_conn
