"""Process-wide singleton connection to ~/.sqlviz/brain.duckdb.

brain.duckdb is shared across all projects in one SQLviz installation —
one file per machine, not one per project.

V0.2 adds three learning tables:
  feedback_patterns — user chart/layout corrections keyed by fingerprint
  layout_patterns   — user layout corrections keyed by fingerprint
  feedback_events   — immutable audit log of every inference and override
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb

if TYPE_CHECKING:
    from sqlviz_inference.contracts.feedback import FeedbackEvent

_brain_conn: duckdb.DuckDBPyConnection | None = None

_BRAIN_APP = "sqlviz-brain"
_BRAIN_VERSION = "0.2.0"


def get_brain_path() -> Path:
    """Return ~/.sqlviz/brain.duckdb, creating ~/.sqlviz/ if needed."""
    brain_dir = Path.home() / ".sqlviz"
    brain_dir.mkdir(parents=True, exist_ok=True)
    return brain_dir / "brain.duckdb"


def _ensure_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create all brain.duckdb tables if they don't exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _brain_meta (
            key   VARCHAR PRIMARY KEY,
            value VARCHAR NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback_patterns (
            fingerprint    VARCHAR PRIMARY KEY,
            field_name     VARCHAR NOT NULL,
            inferred_value VARCHAR NOT NULL,
            user_value     VARCHAR NOT NULL,
            updated_at     VARCHAR NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_patterns (
            fingerprint VARCHAR PRIMARY KEY,
            col_span    INTEGER,
            height_px   INTEGER,
            updated_at  VARCHAR NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback_events (
            id             VARCHAR PRIMARY KEY,
            fingerprint    VARCHAR NOT NULL,
            field_name     VARCHAR NOT NULL,
            inferred_value VARCHAR NOT NULL,
            user_value     VARCHAR NOT NULL,
            panel_id       VARCHAR,
            dashboard_id   VARCHAR,
            created_at     VARCHAR NOT NULL
        )
        """
    )


def get_brain_connection() -> duckdb.DuckDBPyConnection:
    """Return the process-wide singleton connection to brain.duckdb.

    On first call: opens (or creates) brain.duckdb, creates all tables,
    and seeds the identity rows.  Every subsequent call returns the same
    Python object — no new connections are created.
    """
    global _brain_conn
    if _brain_conn is None:
        path = get_brain_path()
        conn = duckdb.connect(str(path))
        _ensure_tables(conn)
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


# ── feedback_patterns ─────────────────────────────────────────────────────────

def get_chart_pattern(
    conn: duckdb.DuckDBPyConnection, fingerprint: str
) -> str | None:
    """Return the learned chart type override for fingerprint, or None."""
    row = conn.execute(
        """
        SELECT user_value FROM feedback_patterns
        WHERE fingerprint = ? AND field_name = 'chart_type'
        """,
        [fingerprint],
    ).fetchone()
    return row[0] if row is not None else None


def record_chart_override(
    conn: duckdb.DuckDBPyConnection,
    fingerprint: str,
    inferred_chart: str,
    user_chart: str,
) -> None:
    """Upsert a chart correction into feedback_patterns."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO feedback_patterns
            (fingerprint, field_name, inferred_value, user_value, updated_at)
        VALUES (?, 'chart_type', ?, ?, ?)
        ON CONFLICT (fingerprint) DO UPDATE SET
            field_name     = excluded.field_name,
            inferred_value = excluded.inferred_value,
            user_value     = excluded.user_value,
            updated_at     = excluded.updated_at
        """,
        [fingerprint, inferred_chart, user_chart, now],
    )


# ── layout_patterns ───────────────────────────────────────────────────────────

def get_layout_pattern(
    conn: duckdb.DuckDBPyConnection, fingerprint: str
) -> dict[str, int] | None:
    """Return {col_span, height_px} for fingerprint, or None."""
    row = conn.execute(
        "SELECT col_span, height_px FROM layout_patterns WHERE fingerprint = ?",
        [fingerprint],
    ).fetchone()
    if row is None:
        return None
    return {"col_span": row[0], "height_px": row[1]}


def record_layout_override(
    conn: duckdb.DuckDBPyConnection,
    fingerprint: str,
    col_span: int | None,
    height_px: int | None,
) -> None:
    """Upsert a layout correction into layout_patterns."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO layout_patterns (fingerprint, col_span, height_px, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (fingerprint) DO UPDATE SET
            col_span   = excluded.col_span,
            height_px  = excluded.height_px,
            updated_at = excluded.updated_at
        """,
        [fingerprint, col_span, height_px, now],
    )


# ── feedback_events ───────────────────────────────────────────────────────────

def log_feedback_event(
    conn: duckdb.DuckDBPyConnection,
    event: "FeedbackEvent",
) -> None:
    """Append an inference or override event to feedback_events."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO feedback_events
            (id, fingerprint, field_name, inferred_value, user_value,
             panel_id, dashboard_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            str(uuid.uuid4()),
            event.fingerprint,
            event.field_name,
            event.inferred_value,
            event.user_value,
            event.panel_id,
            event.dashboard_id,
            now,
        ],
    )
