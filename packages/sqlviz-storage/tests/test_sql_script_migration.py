"""The additive script metadata migration runs on a copy, without guessing IDs."""

from __future__ import annotations

import shutil
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_core.models.sql_reconciliation import CreateSqlPanel
from sqlviz_core.models.sql_script import SqlStatement
from sqlviz_storage.project_db import create_project, open_project
from sqlviz_storage.sql_script_repository import SqlScriptRepository, SqlScriptWriteConflict


def test_migrate_legacy_copy_preserves_original_data_auth_and_unknown_associations(tmp_path):
    original = tmp_path / "original.sqlviz"
    copied = tmp_path / "copy.sqlviz"
    db = create_project(str(original))
    db.execute("DROP TABLE dashboard_sql_scripts")
    db.execute("DELETE FROM schema_migrations WHERE id = '0022_dashboard_sql_scripts'")
    db.execute(
        "INSERT INTO dashboards (id, name, sql_content, created_at, updated_at) "
        "VALUES ('d', 'Dashboard', 'SELECT 1; SELECT 1', 't', 't')"
    )
    db.execute(
        "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at, "
        "view_title, col_span_user_override) "
        "VALUES ('p', 'd', 'P', 'SELECT 1', 't', 't', 'Title', 6)"
    )
    before = {
        table: db.execute(f'SELECT * FROM "{table}"').fetchall()
        for table in ("dashboards", "panels", "_sqlviz_auth")
    }
    db.close()
    shutil.copy2(original, copied)
    migrated = open_project(str(copied))
    try:
        for table, values in before.items():
            assert migrated.execute(f'SELECT * FROM "{table}"').fetchall() == values
        assert migrated.execute("SELECT * FROM dashboard_sql_scripts").fetchall() == []
        assert SqlScriptRepository(migrated).read("d").publication is None
        assert migrated.execute(
            "SELECT count(*) FROM schema_migrations WHERE id = '0022_dashboard_sql_scripts'"
        ).fetchone() == (1,)
    finally:
        migrated.close()
    reopened = open_project(str(copied))
    reopened.close()
    untouched = duckdb.connect(str(original), read_only=True)
    try:
        assert untouched.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'dashboard_sql_scripts'"
        ).fetchone() == (0,)
        for table, values in before.items():
            assert untouched.execute(f'SELECT * FROM "{table}"').fetchall() == values
    finally:
        untouched.close()


@pytest.mark.parametrize("fail", [False, True])
def test_reopen_after_commit_or_failure_never_contains_a_partial_definition(tmp_path, fail):
    path = str(tmp_path / "synthetic.sqlviz")
    db = create_project(path)
    db.execute(
        "INSERT INTO dashboards (id, name, created_at, updated_at) VALUES ('d', 'D', 't', 't')"
    )
    before = SqlScriptRepository(db).read("d")
    proxy = Mock(wraps=db)
    if fail:
        proxy.commit.side_effect = duckdb.TransactionException("failed commit")
    repo = SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy))

    def write():
        return repo.write(
            "d",
            before.revision,
            "SELECT 1",
            [CreateSqlPanel(0, "new")],
            parse=lambda _source: (SqlStatement("SELECT 1", 0, 8),),
        )

    try:
        if fail:
            with pytest.raises(SqlScriptWriteConflict):
                write()
        else:
            result = write()
    finally:
        db.close()
    reopened = open_project(path)
    try:
        snapshot = SqlScriptRepository(reopened).read("d")
        assert snapshot == (before if fail else result.snapshot)
        assert reopened.execute("SELECT count(*) FROM panels").fetchone() == ((0 if fail else 1),)
        assert reopened.execute("SELECT count(*) FROM dashboard_sql_scripts").fetchone() == (
            (0 if fail else 1),
        )
    finally:
        reopened.close()
