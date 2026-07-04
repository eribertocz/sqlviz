"""Tests for secrets.py — DuckDB Secrets wrapper.

Coverage:
  - create_secret registers a secret visible in list_secrets().
  - Passwords NEVER appear in list_secrets() output or in exceptions.
  - delete_secret removes the secret from list_secrets().
  - Input validation rejects unsafe names, unsupported types, bad ports.
  - attach_via_secret is skipped: requires a live external database server.
"""

from __future__ import annotations

from collections.abc import Generator

import duckdb
import pytest
from sqlviz_storage.secrets import (
    attach_via_secret,
    create_secret,
    delete_secret,
    list_secrets,
)

# Sentinel used across tests to verify password non-exposure.
_SECRET_PW = "TOPSECRETPASSWORD_DO_NOT_LEAK"


@pytest.fixture
def conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Fresh in-memory DuckDB connection — no secrets pre-loaded."""
    c = duckdb.connect(":memory:")
    yield c
    c.close()


# ── list_secrets on empty connection ─────────────────────────────────────────

class TestEmptySecrets:

    def test_fresh_connection_has_no_secrets(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        assert list_secrets(conn) == []


# ── create_secret + list_secrets ─────────────────────────────────────────────

class TestCreateAndList:

    def test_secret_name_appears_in_list(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_test", "postgres", "localhost", 5432, "mydb", "user", _SECRET_PW)
        assert "pg_test" in list_secrets(conn)

    def test_multiple_secrets_all_listed(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_one", "postgres", "h1", 5432, "db1", "u1", _SECRET_PW)
        create_secret(conn, "pg_two", "postgres", "h2", 5433, "db2", "u2", _SECRET_PW)
        names = list_secrets(conn)
        assert "pg_one" in names
        assert "pg_two" in names

    def test_replace_existing_secret(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_r", "postgres", "h1", 5432, "db1", "u", _SECRET_PW)
        create_secret(conn, "pg_r", "postgres", "h2", 5432, "db2", "u", _SECRET_PW)
        # OR REPLACE — must not raise; name still present once
        assert list_secrets(conn).count("pg_r") == 1


# ── Password never exposed ────────────────────────────────────────────────────

class TestPasswordNotExposed:

    def test_password_not_in_list_secrets_output(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_safe", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        names = list_secrets(conn)
        for name in names:
            assert _SECRET_PW not in name

    def test_password_not_in_duckdb_secrets_full_row(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_safe2", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        rows = conn.execute("SELECT * FROM duckdb_secrets()").fetchall()
        full_output = str(rows)
        assert _SECRET_PW not in full_output

    def test_password_not_in_runtime_error_on_bad_execute(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        # Trigger the except path by closing the connection mid-create.
        dead = duckdb.connect(":memory:")
        dead.close()
        try:
            create_secret(dead, "x", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        except Exception as exc:
            assert _SECRET_PW not in str(exc)
            assert _SECRET_PW not in repr(exc)


# ── delete_secret ─────────────────────────────────────────────────────────────

class TestDeleteSecret:

    def test_delete_removes_from_list(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_del", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        assert "pg_del" in list_secrets(conn)
        delete_secret(conn, "pg_del")
        assert "pg_del" not in list_secrets(conn)

    def test_delete_nonexistent_raises_runtime_error(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(RuntimeError):
            delete_secret(conn, "does_not_exist")

    def test_delete_only_removes_target(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_keep", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        create_secret(conn, "pg_gone", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        delete_secret(conn, "pg_gone")
        names = list_secrets(conn)
        assert "pg_keep" in names
        assert "pg_gone" not in names


# ── Input validation ──────────────────────────────────────────────────────────

class TestValidation:

    def test_invalid_name_raises_value_error(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError, match="secret name"):
            create_secret(conn, "bad-name!", "postgres", "h", 5432, "db", "u", "pw")

    def test_name_with_sql_injection_raises(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError):
            create_secret(
                conn,
                "x'; DROP TABLE foo; --",
                "postgres", "h", 5432, "db", "u", "pw",
            )

    def test_unsupported_type_raises_value_error(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError, match="Unsupported secret type"):
            create_secret(conn, "s", "oracle", "h", 5432, "db", "u", "pw")

    def test_port_zero_raises_value_error(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError, match="Port"):
            create_secret(conn, "s", "postgres", "h", 0, "db", "u", "pw")

    def test_port_too_high_raises_value_error(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError, match="Port"):
            create_secret(conn, "s", "postgres", "h", 65536, "db", "u", "pw")

    def test_delete_unsafe_name_raises_value_error(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError):
            delete_secret(conn, "bad name!")

    def test_password_not_in_validation_error_message(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        try:
            create_secret(conn, "bad-name!", "postgres", "h", 5432, "db", "u", _SECRET_PW)
        except ValueError as exc:
            assert _SECRET_PW not in str(exc)


# ── attach_via_secret (skipped: requires live server) ────────────────────────

class TestAttachViaSecret:

    @pytest.mark.skip(
        reason=(
            "attach_via_secret requires a live external database server. "
            "The DuckDB ATTACH call succeeds only when the target host is "
            "reachable and the credentials are valid. This test is deferred "
            "to integration testing (Phase 4) where a real PostgreSQL "
            "container can be started alongside the test suite."
        )
    )
    def test_attach_postgres_via_secret(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        create_secret(conn, "pg_live", "postgres", "localhost", 5432, "testdb", "user", "pw")
        attach_via_secret(conn, "live_db", "pg_live", "postgres")
        rows = conn.execute("SELECT table_name FROM information_schema.tables LIMIT 1").fetchall()
        assert isinstance(rows, list)

    def test_attach_input_validation_works_without_server(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError):
            attach_via_secret(conn, "bad alias!", "s", "postgres")

    def test_attach_unsupported_type_raises(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            attach_via_secret(conn, "alias", "secret_name", "oracle")
