"""Schema migration runner for .sqlviz project files.

How it works:
  - MIGRATIONS is an ordered list of (id, sql) tuples.
  - run_migrations(conn) applies every entry whose id is not yet
    recorded in schema_migrations, in list order.
  - Applied migrations are recorded immediately after their SQL runs.
  - A failed migration is logged and skipped; the project remains
    fully usable with the tables that already existed.  The failed
    migration is NOT recorded, so it will be retried on next open.

Adding a migration:
  Append a new (id, sql) tuple to MIGRATIONS.  The id must be unique
  and should follow the convention "NNNN_short_description"
  (e.g. "0001_add_dashboard_description").  Never edit or remove an
  existing entry — always add a new one.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import duckdb

_log = logging.getLogger(__name__)

# ── Migration list ────────────────────────────────────────────────────────────

MIGRATIONS: list[tuple[str, str]] = [
    # 0001: add nonce column to shares (DOC7 §4.1 — per-share nonce enables
    # independent revocation and multiple tokens per dashboard).
    # Fresh databases created after this change already have the column via
    # SCHEMA_STATEMENTS; this migration handles files created before the change.
    (
        "0001_shares_add_nonce",
        "ALTER TABLE shares ADD COLUMN nonce VARCHAR DEFAULT ''",
    ),
]


# ── Runner ────────────────────────────────────────────────────────────────────

def run_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Apply all pending migrations in order.

    Ensures schema_migrations exists (handles pre-runner project files),
    then applies each migration that has not yet been recorded there.

    Args:
        conn: An open, read-write connection to a valid .sqlviz project.
    """
    # Belt-and-suspenders: create the control table if the project predates
    # the migration runner (it is also in SCHEMA_STATEMENTS for new projects).
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id         VARCHAR PRIMARY KEY,
            applied_at VARCHAR NOT NULL
        )
        """
    )

    for migration_id, sql in MIGRATIONS:
        row = conn.execute(
            "SELECT id FROM schema_migrations WHERE id = ?",
            [migration_id],
        ).fetchone()
        if row is not None:
            continue  # already applied

        try:
            conn.execute(sql)
            conn.execute(
                "INSERT INTO schema_migrations VALUES (?, ?)",
                [migration_id, _now_iso()],
            )
            _log.info("Migration %s applied.", migration_id)
        except Exception:
            _log.warning(
                "Migration %s failed — project remains usable without it.",
                migration_id,
                exc_info=True,
            )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
