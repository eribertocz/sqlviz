"""Additive draft generation migration is tested only on copied project files."""

from __future__ import annotations

import shutil

import duckdb
from sqlviz_storage.project_db import create_project, open_project
from sqlviz_storage.sql_draft_repository import SqlDraftRepository

MIGRATION = "0023_dashboard_sql_draft_generation"


def test_legacy_copy_preserves_original_and_does_not_invent_empty_provenance(tmp_path):
    original = tmp_path / "original.sqlviz"
    copied = tmp_path / "copied.sqlviz"
    db = create_project(str(original))
    db.execute("ALTER TABLE dashboards DROP COLUMN sql_draft_generation")
    for key, source in [("saved", "-- 🧠\r\nSELECT 'unfinished"), ("empty", "")]:
        db.execute(
            "INSERT INTO dashboards (id, name, sql_content, created_at, updated_at, "
            "last_run_at, last_run_sql) VALUES (?, ?, ?, 't', 't', 'last', 'prior')",
            [key, key, source],
        )
    db.execute(
        "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at, "
        "view_title, col_span_user_override) "
        "VALUES ('p', 'saved', 'P', 'SELECT 1', 't', 't', 'Title', 6)"
    )
    before = {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
              for table in ("dashboards", "panels", "_sqlviz_auth", "dashboard_sql_scripts")}
    db.close()
    shutil.copy2(original, copied)
    migrated = open_project(str(copied))
    try:
        for table, values in before.items():
            actual = migrated.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            assert actual == ([(*row, 0) for row in values] if table == "dashboards" else values)
        repo = SqlDraftRepository(migrated)
        saved, empty = repo.read("saved"), repo.read("empty")
        assert saved.source == "-- 🧠\r\nSELECT 'unfinished" and saved.generation == 0
        assert empty.source == "" and not empty.initialized
        assert migrated.execute(
            "SELECT count(*) FROM schema_migrations WHERE id = ?", [MIGRATION],
        ).fetchone() == (1,)
        assert next(row for row in migrated.execute("DESCRIBE dashboards").fetchall()
                    if row[0] == "sql_draft_generation")[2] == "NO"
        written = repo.write("empty", empty.revision, "")
    finally:
        migrated.close()
    reopened = open_project(str(copied))
    try:
        assert SqlDraftRepository(reopened).read("empty") == written
        assert written.initialized and written.generation == 1
        assert reopened.execute(
            "SELECT count(*) FROM schema_migrations WHERE id = ?", [MIGRATION],
        ).fetchone() == (1,)
    finally:
        reopened.close()
    untouched = duckdb.connect(str(original), read_only=True)
    try:
        assert "sql_draft_generation" not in [row[0] for row in
                                                untouched.execute("DESCRIBE dashboards").fetchall()]
        for table, values in before.items():
            assert untouched.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall() == values
    finally:
        untouched.close()
