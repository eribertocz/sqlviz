"""Create and open .sqlviz project files (DOC2 Section 4).

A .sqlviz file is a standard DuckDB database containing:
  - 8 application tables defined in schema.py
  - A _sqlviz_meta signature row ('app' = 'sqlviz')
  - A single _sqlviz_auth row with a generated session_secret

Public API:
  create_project(path) -> DuckDBPyConnection
  open_project(path)   -> DuckDBPyConnection
  is_sqlviz_project(path) -> bool
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from .migrations import run_migrations
from .schema import SCHEMA_STATEMENTS

_APP_NAME = "sqlviz"
_APP_VERSION = "0.1.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _is_initialized(conn: duckdb.DuckDBPyConnection) -> bool:
    """True when the _sqlviz_meta 'app' row is present and correct."""
    try:
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
        return row is not None and row[0] == _APP_NAME
    except Exception:  # noqa: BLE001
        return False


def is_sqlviz_project(path: str | Path) -> bool:
    """Return True if *path* is an existing, valid .sqlviz project file.

    Opens the file read-only; never raises — returns False on any error.
    """
    p = Path(path)
    if not p.exists():
        return False
    try:
        conn = duckdb.connect(str(p), read_only=True)
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
        conn.close()
        return row is not None and row[0] == _APP_NAME
    except Exception:  # noqa: BLE001
        return False


def create_project(path: str) -> duckdb.DuckDBPyConnection:
    """Create (or reopen) a .sqlviz project file.

    - If the file does not exist it is created, all 8 schema tables are
      written, and the _sqlviz_meta signature + session_secret are seeded.
    - If the file already exists and is a valid .sqlviz project, it is
      opened without touching the schema or resetting the session_secret.
    - The schema statements use CREATE TABLE IF NOT EXISTS so replaying
      them against an existing file is always safe.

    Args:
        path: Filesystem path for the .sqlviz file.

    Returns:
        An open, read-write DuckDB connection to the project file.
    """
    conn = duckdb.connect(str(path))

    for stmt in SCHEMA_STATEMENTS:
        conn.execute(stmt)

    if not _is_initialized(conn):
        now = _now_iso()
        conn.execute("INSERT INTO _sqlviz_meta VALUES ('app', ?)", [_APP_NAME])
        conn.execute("INSERT INTO _sqlviz_meta VALUES ('version', ?)", [_APP_VERSION])
        conn.execute("INSERT INTO _sqlviz_meta VALUES ('created', ?)", [now])
        # password_hash starts empty; the CLI/API sets it on first-time setup.
        conn.execute(
            "INSERT INTO _sqlviz_auth VALUES (?, ?, ?, ?)",
            ["", secrets.token_urlsafe(32), now, now],
        )

    return conn


def open_project(path: str) -> duckdb.DuckDBPyConnection:
    """Open an existing .sqlviz project file without modifying its schema.

    The schema migration path (CREATE/ALTER TABLE) belongs to the
    migration runner (project_db 3.2) — this function intentionally
    skips schema execution.

    Args:
        path: Filesystem path of an existing .sqlviz file.

    Returns:
        An open, read-write DuckDB connection to the project file.

    Raises:
        FileNotFoundError: The file does not exist at *path*.
        ValueError: The file exists but is not a valid .sqlviz project.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Project file not found: {path}")

    try:
        conn = duckdb.connect(str(p))
    except Exception as exc:
        raise ValueError(f"Not a valid .sqlviz project: {path}") from exc

    try:
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
    except Exception as exc:
        conn.close()
        raise ValueError(f"Not a valid .sqlviz project: {path}") from exc

    if row is None or row[0] != _APP_NAME:
        conn.close()
        raise ValueError(f"Not a valid .sqlviz project: {path}")

    run_migrations(conn)
    return conn
