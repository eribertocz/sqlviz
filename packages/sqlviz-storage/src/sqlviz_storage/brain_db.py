"""Process-wide singleton connection to ~/.sqlviz/brain.duckdb.

brain.duckdb is shared across all projects in one SQLviz installation —
one file per machine, not one per project. Learning tables (sql_patterns,
layout_patterns, etc.) are deferred to V0.3; for V0.1 the file exists
only to establish the infrastructure and carry its identity signature.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

_brain_conn: duckdb.DuckDBPyConnection | None = None

_BRAIN_APP = "sqlviz-brain"
_BRAIN_VERSION = "0.1.0"


def get_brain_path() -> Path:
    """Return ~/.sqlviz/brain.duckdb, creating ~/.sqlviz/ if needed."""
    brain_dir = Path.home() / ".sqlviz"
    brain_dir.mkdir(parents=True, exist_ok=True)
    return brain_dir / "brain.duckdb"


def get_brain_connection() -> duckdb.DuckDBPyConnection:
    """Return the process-wide singleton connection to brain.duckdb.

    On first call: opens (or creates) brain.duckdb, creates _brain_meta,
    and seeds the identity rows.  Every subsequent call returns the same
    Python object — no new connections are created.
    """
    global _brain_conn
    if _brain_conn is None:
        path = get_brain_path()
        conn = duckdb.connect(str(path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _brain_meta (
                key   VARCHAR PRIMARY KEY,
                value VARCHAR NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT value FROM _brain_meta WHERE key = 'app'"
        ).fetchone()
        if row is None:
            conn.execute("INSERT INTO _brain_meta VALUES ('app', ?)", [_BRAIN_APP])
            conn.execute(
                "INSERT INTO _brain_meta VALUES ('version', ?)", [_BRAIN_VERSION]
            )
        _brain_conn = conn
    return _brain_conn
