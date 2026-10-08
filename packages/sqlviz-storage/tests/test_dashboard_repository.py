"""Deletion, rollback, persistence and competing writes on real DuckDB cursors."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
import sqlviz_storage.dashboard_repository as repository_module
from sqlviz_storage.dashboard_repository import (
    DashboardNotFound,
    DashboardRepository,
    DashboardWriteConflict,
    dashboard_write,
)
from sqlviz_storage.project_db import create_project, open_project


def seed(db: duckdb.DuckDBPyConnection) -> None:
    for key in ("a", "b"):
        db.execute(
            "INSERT INTO dashboards (id, name, created_at, updated_at) VALUES (?, ?, 't', 't')",
            [key, key],
        )
        db.execute(
            "INSERT INTO panels (id, dashboard_id, name, created_at, updated_at) "
            "VALUES (?, ?, ?, 't', 't')", [key, key, key],
        )
        db.execute("INSERT INTO filter_memory VALUES (?, 'region', 'North', 't')", [key])
        db.execute(
            "INSERT INTO shares VALUES (?, ?, 'nonce', ?, 'public', NULL, 't', false)",
            [key, key, "token-" + key],
        )
    db.execute(
        "INSERT INTO shares VALUES ('workspace', '__workspace__', 'nonce', 'workspace-token', "
        "'public', NULL, 't', false)",
    )
    db.execute("CREATE TABLE sales (amount INTEGER)")
    db.execute("INSERT INTO sales VALUES (42)")


@pytest.fixture
def db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    conn = create_project(":memory:")
    seed(conn)
    yield conn
    conn.close()


def snapshot(db: duckdb.DuckDBPyConnection) -> dict[str, list[tuple]]:
    return {
        table: db.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall()
        for table in ("dashboards", "panels", "shares", "filter_memory", "sales", "_sqlviz_auth")
    }


def test_delete_removes_only_owned_rows_and_hides_tokens_in_repr(db) -> None:
    before = snapshot(db)
    result = DashboardRepository(db).delete("a")
    assert result.share_tokens == ("token-a",)
    assert "token-a" not in repr(result)
    for table in ("dashboards", "panels", "shares", "filter_memory"):
        assert db.execute(f'SELECT count(*) FROM "{table}" WHERE '
                          f'{"id" if table == "dashboards" else "dashboard_id"} = ?',
                          ["a"]).fetchone() == (0,)
        assert db.execute(f'SELECT * FROM "{table}" WHERE '
                          f'{"id" if table == "dashboards" else "dashboard_id"} = ?',
                          ["b"]).fetchall() == [row for row in before[table] if row[0] == "b"]
    assert db.execute("SELECT token FROM shares WHERE id = 'workspace'").fetchone() == (
        "workspace-token",
    )
    assert snapshot(db)["sales"] == before["sales"]
    assert snapshot(db)["_sqlviz_auth"] == before["_sqlviz_auth"]


def test_missing_parent_rolls_back_and_cursor_can_be_reused(db) -> None:
    before = snapshot(db)
    with pytest.raises(DashboardNotFound):
        DashboardRepository(db).delete("missing")
    assert snapshot(db) == before
    DashboardRepository(db).delete("a")


@pytest.mark.parametrize("table", ["panels", "shares", "filter_memory"])
def test_real_database_failure_at_each_child_stage_rolls_back_all_rows(db, table) -> None:
    # A legacy/corrupt schema exposes a read-only view. DELETE fails at the
    # selected stage, after earlier deletes have already happened in the tx.
    db.execute(f'ALTER TABLE "{table}" RENAME TO "saved_{table}"')
    db.execute(f'CREATE VIEW "{table}" AS SELECT * FROM "saved_{table}"')
    before = snapshot(db)
    with pytest.raises(duckdb.Error):
        DashboardRepository(db).delete("a")
    assert snapshot(db) == before


def test_parent_constraint_failure_rolls_back_children(db) -> None:
    db.execute("CREATE TABLE retained (dashboard_id VARCHAR REFERENCES dashboards(id))")
    db.execute("INSERT INTO retained VALUES ('a')")
    before = snapshot(db)
    with pytest.raises(DashboardWriteConflict):
        DashboardRepository(db).delete("a")
    assert snapshot(db) == before
    db.execute("DELETE FROM retained")
    DashboardRepository(db).delete("a")


def test_commit_failure_never_returns_deletion_result(db) -> None:
    before = snapshot(db)
    cursor = Mock(wraps=db)
    cursor.commit.side_effect = duckdb.TransactionException("synthetic commit conflict")
    with pytest.raises(DashboardWriteConflict):
        DashboardRepository(cast(duckdb.DuckDBPyConnection, cursor)).delete("a")
    assert snapshot(db) == before


@pytest.mark.parametrize("fail", [False, True])
def test_reopened_file_contains_complete_committed_or_rolled_back_state(
    tmp_path: Path, fail,
) -> None:
    path = tmp_path / "synthetic.sqlviz"
    conn = create_project(str(path))
    try:
        seed(conn)
        if fail:
            conn.execute("CREATE TABLE retained (dashboard_id VARCHAR REFERENCES dashboards(id))")
            conn.execute("INSERT INTO retained VALUES ('a')")
        before = snapshot(conn)
        if fail:
            with pytest.raises(DashboardWriteConflict):
                DashboardRepository(conn).delete("a")
        else:
            DashboardRepository(conn).delete("a")
        after = snapshot(conn)
    finally:
        conn.close()
    reopened = open_project(str(path))
    try:
        assert snapshot(reopened) == after
        if fail:
            assert after == before
        else:
            assert reopened.execute("SELECT id FROM dashboards ORDER BY id").fetchall() == [("b",)]
    finally:
        reopened.close()


def test_other_cursor_sees_complete_snapshot_until_commit(db) -> None:
    writer, reader = db.cursor(), db.cursor()
    try:
        reader.begin()
        before = snapshot(reader)
        DashboardRepository(writer).delete("a")
        assert snapshot(reader) == before
        reader.commit()
        assert reader.execute("SELECT id FROM dashboards ORDER BY id").fetchall() == [("b",)]
        assert reader.execute("SELECT id FROM panels ORDER BY id").fetchall() == [("b",)]
    finally:
        writer.close()
        reader.close()


def insert_panel(db: duckdb.DuckDBPyConnection, key: str, parent: str = "a") -> None:
    db.execute(
        "INSERT INTO panels (id, dashboard_id, name, created_at, updated_at) "
        "VALUES (?, ?, 'new', 't', 't')", [key, parent],
    )


def test_child_creation_conflicts_with_uncommitted_deletion_and_retry_gets_missing(db) -> None:
    deleting, creating = db.cursor(), db.cursor()
    try:
        with dashboard_write(deleting, "a"):
            # All child creation paths fence the same parent before INSERT.
            with pytest.raises(DashboardWriteConflict):
                with dashboard_write(creating, "a"):
                    insert_panel(creating, "late")
            deleting.execute("DELETE FROM panels WHERE dashboard_id = 'a'")
            deleting.execute("DELETE FROM shares WHERE dashboard_id = 'a'")
            deleting.execute("DELETE FROM filter_memory WHERE dashboard_id = 'a'")
            deleting.execute("DELETE FROM dashboards WHERE id = 'a'")
        with pytest.raises(DashboardNotFound):
            with dashboard_write(creating, "a"):
                insert_panel(creating, "late")
        assert creating.execute("SELECT id FROM panels WHERE dashboard_id = 'a'").fetchall() == []
    finally:
        deleting.close()
        creating.close()


def test_deletion_conflicts_with_creation_then_retry_removes_new_child(db) -> None:
    creating, deleting = db.cursor(), db.cursor()
    try:
        with dashboard_write(creating, "a"):
            insert_panel(creating, "new")
            with pytest.raises(DashboardWriteConflict):
                DashboardRepository(deleting).delete("a")
        assert db.execute("SELECT id FROM panels WHERE id = 'new'").fetchone() == ("new",)
        DashboardRepository(deleting).delete("a")
        assert db.execute("SELECT id FROM panels WHERE dashboard_id = 'a'").fetchall() == []
    finally:
        creating.close()
        deleting.close()


def test_unrelated_dashboard_can_be_deleted_during_child_creation(db) -> None:
    creating, deleting = db.cursor(), db.cursor()
    try:
        with dashboard_write(creating, "a"):
            insert_panel(creating, "new")
            DashboardRepository(deleting).delete("b")
        assert db.execute("SELECT id FROM dashboards").fetchall() == [("a",)]
        assert db.execute("SELECT id FROM panels ORDER BY id").fetchall() == [("a",), ("new",)]
        assert db.execute("SELECT updated_at FROM dashboards").fetchone() != ("t",)
    finally:
        creating.close()
        deleting.close()


def test_failure_while_creating_child_restores_parent_and_leaves_no_child(db) -> None:
    before = snapshot(db)
    with pytest.raises(RuntimeError, match="synthetic"):
        with dashboard_write(db, "a"):
            insert_panel(db, "new")
            raise RuntimeError("synthetic write failure")
    assert snapshot(db) == before


def test_equal_clock_value_still_performs_a_real_parent_write(db, monkeypatch) -> None:
    fixed = datetime(2026, 10, 6, tzinfo=timezone.utc)

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(repository_module, "datetime", FixedClock)
    db.execute("UPDATE dashboards SET updated_at = ? WHERE id = 'a'", [fixed.isoformat()])
    # Use exactly the same microsecond format the writer will produce.
    db.execute("UPDATE dashboards SET updated_at = ? WHERE id = 'a'",
               [fixed.isoformat(timespec="microseconds")])
    writer, competing = db.cursor(), db.cursor()
    try:
        with dashboard_write(writer, "a"):
            with pytest.raises(DashboardWriteConflict):
                DashboardRepository(competing).delete("a")
        assert db.execute("SELECT updated_at FROM dashboards WHERE id = 'a'").fetchone() == (
            "2026-10-06T00:00:00.000001+00:00",
        )
    finally:
        writer.close()
        competing.close()


def test_delete_committed_between_parent_read_and_update_cannot_create_orphan(db) -> None:
    writing, deleting = db.cursor(), db.cursor()
    original_execute = writing.execute
    proxy = Mock(wraps=writing)

    def execute(sql, parameters):
        if sql.startswith("UPDATE dashboards"):
            # dashboard_write already read the parent in its transaction;
            # another cursor now deletes and commits before its UPDATE.
            DashboardRepository(deleting).delete("a")
        return original_execute(sql, parameters)

    proxy.execute.side_effect = execute
    try:
        with pytest.raises(DashboardWriteConflict):
            with dashboard_write(cast(duckdb.DuckDBPyConnection, proxy), "a"):
                insert_panel(writing, "orphan")
        assert db.execute("SELECT id FROM dashboards WHERE id = 'a'").fetchall() == []
        assert db.execute("SELECT id FROM panels WHERE dashboard_id = 'a'").fetchall() == []
    finally:
        writing.close()
        deleting.close()
