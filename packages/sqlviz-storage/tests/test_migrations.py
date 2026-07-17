"""Tests for the migration runner (migrations.py).

Scenarios:
  - Fresh project has no applied migrations after open_project.
  - A valid migration is applied exactly once across multiple opens.
  - The migrated column actually exists in the table afterwards.
  - An invalid migration does not prevent open_project from returning
    a usable connection.
  - Multiple migrations apply in order; already-applied ones are skipped.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import sqlviz_storage.migrations as mig_module
from sqlviz_storage.project_db import create_project, open_project

# ── Helpers ───────────────────────────────────────────────────────────────────

def _applied_ids(conn: duckdb.DuckDBPyConnection) -> list[str]:
    rows = conn.execute("SELECT id FROM schema_migrations ORDER BY applied_at").fetchall()
    return [row[0] for row in rows]


def _column_names(conn: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    rows = conn.execute(f"DESCRIBE {table}").fetchall()
    return [row[0] for row in rows]


# ── Baseline: no migrations ───────────────────────────────────────────────────

class TestNoMigrations:
    # DDL migrations (0001-0014) fail on fresh projects because SCHEMA_STATEMENTS
    # already creates all columns. Data migrations that succeed (e.g., 0015
    # backfill schema_version) are recorded even on fresh projects.

    def test_fresh_project_has_only_data_migrations(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()
        conn = open_project(p)
        ids = _applied_ids(conn)
        conn.close()
        # Only 0015 (data migration: INSERT ON CONFLICT DO NOTHING) succeeds
        # on a fresh project. DDL migrations fail because columns already exist.
        assert ids == ["0015_meta_set_schema_version"]

    def test_schema_migrations_table_exists_after_open(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()
        conn = open_project(p)
        # Table must be queryable (no exception)
        count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        conn.close()
        # 0015 (data migration) is recorded on fresh projects
        assert count is not None and count[0] == 1


# ── Single migration ──────────────────────────────────────────────────────────

class TestSingleMigration:

    _MIG: list[tuple[str, str]] = [
        ("0001_add_test_col", "ALTER TABLE settings ADD COLUMN test_col VARCHAR"),
    ]

    def test_migration_is_applied_on_first_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIG)

        conn = open_project(p)
        ids = _applied_ids(conn)
        conn.close()
        assert ids == ["0001_add_test_col"]

    def test_migration_column_actually_added(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIG)

        conn = open_project(p)
        cols = _column_names(conn, "settings")
        conn.close()
        assert "test_col" in cols

    def test_migration_not_reapplied_on_second_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIG)

        open_project(p).close()  # first open — applies migration

        conn = open_project(p)   # second open — must not re-apply
        count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        conn.close()
        assert count is not None and count[0] == 1

    def test_migration_not_reapplied_on_third_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIG)

        for _ in range(3):
            open_project(p).close()

        conn = open_project(p)
        count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        conn.close()
        assert count is not None and count[0] == 1


# ── Multiple migrations ───────────────────────────────────────────────────────

class TestMultipleMigrations:

    _MIGS: list[tuple[str, str]] = [
        ("0001_add_col_a", "ALTER TABLE settings ADD COLUMN col_a VARCHAR"),
        ("0002_add_col_b", "ALTER TABLE settings ADD COLUMN col_b VARCHAR"),
    ]

    def test_both_migrations_applied_in_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIGS)

        conn = open_project(p)
        ids = _applied_ids(conn)
        cols = _column_names(conn, "settings")
        conn.close()

        assert ids == ["0001_add_col_a", "0002_add_col_b"]
        assert "col_a" in cols and "col_b" in cols

    def test_only_new_migration_applied_on_second_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        # First open: apply only the first migration
        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIGS[:1])
        open_project(p).close()

        # Second open: add second migration — only it should be applied
        monkeypatch.setattr(mig_module, "MIGRATIONS", self._MIGS)
        conn = open_project(p)
        ids = _applied_ids(conn)
        conn.close()

        assert ids == ["0001_add_col_a", "0002_add_col_b"]


# ── Failed migration ──────────────────────────────────────────────────────────

class TestFailedMigration:

    _BAD: list[tuple[str, str]] = [
        ("0001_invalid", "ALTER TABLE nonexistent_table ADD COLUMN foo VARCHAR"),
    ]

    def test_invalid_migration_does_not_crash_open(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._BAD)

        conn = open_project(p)  # must NOT raise
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
        conn.close()
        assert row is not None and row[0] == "sqlviz"

    def test_failed_migration_not_recorded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        monkeypatch.setattr(mig_module, "MIGRATIONS", self._BAD)

        conn = open_project(p)
        ids = _applied_ids(conn)
        conn.close()
        assert ids == []

    def test_good_migration_after_bad_still_applies(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()

        mixed: list[tuple[str, str]] = [
            ("0001_bad",  "ALTER TABLE nonexistent ADD COLUMN x VARCHAR"),
            ("0002_good", "ALTER TABLE settings ADD COLUMN extra VARCHAR"),
        ]
        monkeypatch.setattr(mig_module, "MIGRATIONS", mixed)

        conn = open_project(p)
        ids = _applied_ids(conn)
        cols = _column_names(conn, "settings")
        conn.close()

        assert "0001_bad" not in ids
        assert "0002_good" in ids
        assert "extra" in cols
