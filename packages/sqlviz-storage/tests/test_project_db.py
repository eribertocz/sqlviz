"""Tests for project_db: create, open, and validate .sqlviz project files.

Coverage:
  - create_project produces a file with all 8 tables and the correct
    _sqlviz_meta signature.
  - create_project on an existing valid file reopens it without
    re-seeding the schema or session_secret.
  - session_secret is generated once at creation and persists across
    subsequent open calls.
  - Each table has exactly the columns specified in DOC2 Section 4.
  - open_project raises FileNotFoundError / ValueError for missing or
    invalid files.
  - is_sqlviz_project returns True/False correctly.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import duckdb
import pytest
from sqlviz_storage.project_db import create_project, is_sqlviz_project, open_project

# ── Helpers ───────────────────────────────────────────────────────────────────

def _column_names(conn: duckdb.DuckDBPyConnection, table: str) -> list[str]:
    rows = conn.execute(f"DESCRIBE {table}").fetchall()
    return [row[0] for row in rows]


# ── Creation ──────────────────────────────────────────────────────────────────

class TestCreateProject:

    def test_creates_file_on_disk(self, tmp_path: Path) -> None:
        p = str(tmp_path / "my.sqlviz")
        conn = create_project(p)
        conn.close()
        assert (tmp_path / "my.sqlviz").exists()

    def test_returns_open_connection(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "p.sqlviz"))
        row = conn.execute("SELECT 1").fetchone()
        conn.close()
        assert row == (1,)

    def test_idempotent_does_not_reset_created_timestamp(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")

        conn1 = create_project(p)
        created = conn1.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'created'"
        ).fetchone()
        conn1.close()
        assert created is not None

        conn2 = create_project(p)
        created2 = conn2.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'created'"
        ).fetchone()
        conn2.close()
        assert created2 is not None

        assert created[0] == created2[0]


# ── _sqlviz_meta signature ────────────────────────────────────────────────────

class TestMetaSignature:

    def test_app_row_is_sqlviz(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "p.sqlviz"))
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
        conn.close()
        assert row is not None and row[0] == "sqlviz"

    def test_version_row(self, tmp_path: Path) -> None:
        from sqlviz_storage.project_db import APP_VERSION

        conn = create_project(str(tmp_path / "p.sqlviz"))
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'version'"
        ).fetchone()
        conn.close()
        assert row is not None and row[0] == APP_VERSION

    def test_schema_version_row(self, tmp_path: Path) -> None:
        from sqlviz_storage.project_db import SCHEMA_VERSION

        conn = create_project(str(tmp_path / "p.sqlviz"))
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'schema_version'"
        ).fetchone()
        conn.close()
        assert row is not None and row[0] == SCHEMA_VERSION

    def test_created_row_is_parseable_iso(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "p.sqlviz"))
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'created'"
        ).fetchone()
        conn.close()
        assert row is not None
        datetime.fromisoformat(row[0])  # raises ValueError if not valid ISO


# ── Session secret ────────────────────────────────────────────────────────────

class TestSessionSecret:

    def test_session_secret_is_non_empty(self, tmp_path: Path) -> None:
        conn = create_project(str(tmp_path / "p.sqlviz"))
        row = conn.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        conn.close()
        assert row is not None and len(row[0]) > 0

    def test_session_secret_persists_across_reopens(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")

        conn1 = create_project(p)
        secret1 = conn1.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        conn1.close()
        assert secret1 is not None

        conn2 = create_project(p)
        secret2 = conn2.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        conn2.close()
        assert secret2 is not None

        assert secret1[0] == secret2[0]

    def test_session_secrets_differ_across_projects(self, tmp_path: Path) -> None:
        conn_a = create_project(str(tmp_path / "a.sqlviz"))
        conn_b = create_project(str(tmp_path / "b.sqlviz"))
        row_a = conn_a.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        row_b = conn_b.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        conn_a.close()
        conn_b.close()
        assert row_a is not None and row_b is not None
        assert row_a[0] != row_b[0]


# ── open_project ──────────────────────────────────────────────────────────────

class TestOpenProject:

    def test_opens_existing_project(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()
        conn = open_project(p)
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
        conn.close()
        assert row is not None and row[0] == "sqlviz"

    def test_raises_for_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            open_project(str(tmp_path / "missing.sqlviz"))

    def test_raises_for_corrupt_file(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.sqlviz"
        p.write_bytes(b"\x00\x01\x02 not a duckdb file \xff")
        with pytest.raises(ValueError):
            open_project(str(p))

    def test_does_not_reseed_session_secret(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")
        conn1 = create_project(p)
        secret1 = conn1.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        conn1.close()
        assert secret1 is not None

        conn2 = open_project(p)
        secret2 = conn2.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
        conn2.close()
        assert secret2 is not None

        assert secret1[0] == secret2[0]


# ── is_sqlviz_project ─────────────────────────────────────────────────────────

class TestIsValidProject:

    def test_valid_project_returns_true(self, tmp_path: Path) -> None:
        p = str(tmp_path / "p.sqlviz")
        create_project(p).close()
        assert is_sqlviz_project(p) is True

    def test_missing_file_returns_false(self, tmp_path: Path) -> None:
        assert is_sqlviz_project(str(tmp_path / "nope.sqlviz")) is False

    def test_corrupt_file_returns_false(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.sqlviz"
        p.write_bytes(b"garbage")
        assert is_sqlviz_project(str(p)) is False


# ── Schema columns (DOC2 Section 4) ──────────────────────────────────────────

class TestSchemaColumns:

    @pytest.fixture
    def conn(self, tmp_path: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        c = create_project(str(tmp_path / "p.sqlviz"))
        yield c
        c.close()

    def test_all_eight_tables_exist(self, conn: duckdb.DuckDBPyConnection) -> None:
        expected = {
            "_sqlviz_meta", "_sqlviz_auth", "connections", "folders",
            "dashboards", "shares", "filter_memory", "settings",
        }
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'"
        ).fetchall()
        found = {row[0] for row in rows}
        assert expected.issubset(found)

    def test_meta_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "_sqlviz_meta") == ["key", "value"]

    def test_auth_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "_sqlviz_auth") == [
            "password_hash", "session_secret", "created_at", "updated_at",
        ]

    def test_connections_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "connections") == [
            "id", "name", "type", "config", "created_at",
        ]

    def test_folders_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "folders") == [
            "id", "name", "parent_id", "sort_order", "created_at",
        ]

    def test_dashboards_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "dashboards") == [
            "id", "name", "folder_id", "connection_id",
            "sql_content", "sort_order", "created_at", "updated_at",
            "dashboard_hint", "dashboard_domain", "description", "last_run_at",
        ]

    def test_shares_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "shares") == [
            "id", "dashboard_id", "nonce", "token", "mode",
            "password_hash", "created_at", "revoked",
        ]

    def test_filter_memory_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "filter_memory") == [
            "dashboard_id", "variable", "value", "updated_at",
        ]

    def test_settings_columns(self, conn: duckdb.DuckDBPyConnection) -> None:
        assert _column_names(conn, "settings") == ["key", "value", "updated_at"]
