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
    # 0002–0011: V0.2 Fase E — override columns on panels (DOC10 §6.14).
    # fingerprint links panels to brain.duckdb patterns.
    # inferred_* are written once on execute; never overwritten.
    # selected_* starts equal to inferred_*; updated when user overrides.
    # *_user_override is NULL until the user explicitly corrects a field.
    ("0002_panels_add_fingerprint",
     "ALTER TABLE panels ADD COLUMN fingerprint VARCHAR"),
    ("0003_panels_add_inferred_chart_type",
     "ALTER TABLE panels ADD COLUMN inferred_chart_type VARCHAR"),
    ("0004_panels_add_selected_chart_type",
     "ALTER TABLE panels ADD COLUMN selected_chart_type VARCHAR"),
    ("0005_panels_add_chart_user_override",
     "ALTER TABLE panels ADD COLUMN chart_user_override VARCHAR"),
    ("0006_panels_add_inferred_col_span",
     "ALTER TABLE panels ADD COLUMN inferred_col_span INTEGER"),
    ("0007_panels_add_selected_col_span",
     "ALTER TABLE panels ADD COLUMN selected_col_span INTEGER"),
    ("0008_panels_add_col_span_user_override",
     "ALTER TABLE panels ADD COLUMN col_span_user_override INTEGER"),
    ("0009_panels_add_inferred_height_px",
     "ALTER TABLE panels ADD COLUMN inferred_height_px INTEGER"),
    ("0010_panels_add_selected_height_px",
     "ALTER TABLE panels ADD COLUMN selected_height_px INTEGER"),
    ("0011_panels_add_height_user_override",
     "ALTER TABLE panels ADD COLUMN height_user_override INTEGER"),
    # 0012–0013: dashboard classification (sidebar icons, DOC6 §12)
    # dashboard_hint   — fine-grained semantic label (e.g. "user_retention")
    # dashboard_domain — coarse category  (e.g. "product", "finance")
    ("0012_dashboards_add_dashboard_hint",
     "ALTER TABLE dashboards ADD COLUMN dashboard_hint VARCHAR"),
    ("0013_dashboards_add_dashboard_domain",
     "ALTER TABLE dashboards ADD COLUMN dashboard_domain VARCHAR"),
    # 0014: store intent_winner per panel so the classifier can use it
    ("0014_panels_add_inferred_intent_type",
     "ALTER TABLE panels ADD COLUMN inferred_intent_type VARCHAR"),
    # 0015: v0.2.4 — backfill schema_version in _sqlviz_meta for existing projects.
    # New projects have this key set by create_project(); this migration handles
    # files created before v0.2.4.
    ("0015_meta_set_schema_version",
     "INSERT INTO _sqlviz_meta VALUES ('schema_version', '1') ON CONFLICT DO NOTHING"),
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
