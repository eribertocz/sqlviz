"""Dashboard PATCH invariants on real transactions and independent cursors."""

from __future__ import annotations

from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_storage.dashboard_repository import (
    DashboardNotFound,
    DashboardRepository,
    DashboardWriteConflict,
    dashboard_write,
)
from sqlviz_storage.folder_repository import FolderRepository, FolderWriteConflict
from sqlviz_storage.project_db import create_project, open_project


def seed(db):
    folder = FolderRepository(db).create("Group").id
    for key in ("a", "b"):
        db.execute(
            "INSERT INTO dashboards (id, name, folder_id, description, created_at, updated_at) "
            "VALUES (?, ?, ?, 'Keep', 'created', 'before')", [key, key, folder],
        )
    return folder


@pytest.fixture
def db():
    conn = create_project(":memory:")
    seed(conn)
    try:
        yield conn
    finally:
        conn.close()


def snapshot(db):
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("dashboards", "folders", "_sqlviz_meta")}


def test_direct_repository_calls_cannot_bypass_policy_or_mutate_input(db):
    before = snapshot(db)
    changes = {"name": "After", "folder_id": None, "sort_order": True}
    with pytest.raises(ValueError):
        DashboardRepository(db).update("a", changes)
    assert snapshot(db) == before
    changes = {"description": "", "sql_content": ""}
    result = DashboardRepository(db).update("a", changes)
    assert result.description is None and result.sql_content == ""
    assert changes == {"description": "", "sql_content": ""}


def test_empty_or_missing_patch_does_not_write(db):
    before = snapshot(db)
    repository = DashboardRepository(db)
    assert repository.update("a", {}) == repository.get("a")
    with pytest.raises(DashboardNotFound):
        repository.update("missing", {})
    with pytest.raises(DashboardNotFound):
        repository.update("missing", {"name": "After", "folder_id": None})
    assert snapshot(db) == before


def test_invalid_destination_rolls_back_other_fields_and_tree_revision(db):
    from sqlviz_core.models.folders import FolderError

    before = snapshot(db)
    with pytest.raises(FolderError) as error:
        DashboardRepository(db).update("a", {"name": "After", "folder_id": "missing"})
    assert error.value.code == "folder_parent_not_found"
    assert snapshot(db) == before


def test_read_after_write_failure_rolls_back_fields_timestamp_and_placement(db):
    before = snapshot(db)
    proxy = Mock(wraps=db)
    wrote = False

    def execute(sql, parameters):
        nonlocal wrote
        if wrote and sql.startswith("SELECT id, name"):
            raise RuntimeError("synthetic read failure")
        if sql.startswith("UPDATE dashboards"):
            wrote = True
        return db.execute(sql, parameters)

    proxy.execute.side_effect = execute
    with pytest.raises(RuntimeError, match="synthetic read failure"):
        DashboardRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
            "a", {"name": "After", "folder_id": None},
        )
    assert snapshot(db) == before


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("placement", [False, True])
def test_reopened_file_has_only_a_complete_committed_or_rolled_back_patch(
    tmp_path, fail, placement,
):
    path = str(tmp_path / "synthetic.sqlviz")
    conn = create_project(path)
    try:
        seed(conn)
        before = snapshot(conn)
        unchanged = DashboardRepository(conn).get("b")
        changes = {"name": "After", "description": None, "sql_content": "-- ñ\r\nSELECT 1;\n"}
        if placement:
            changes["folder_id"] = None
        proxy = Mock(wraps=conn)
        if fail:
            proxy.commit.side_effect = duckdb.TransactionException("synthetic commit conflict")
            with pytest.raises(FolderWriteConflict if placement else DashboardWriteConflict):
                DashboardRepository(cast(duckdb.DuckDBPyConnection, proxy)).update("a", changes)
        else:
            result = DashboardRepository(conn).update("a", changes)
        after = snapshot(conn)
    finally:
        conn.close()
    reopened = open_project(path)
    try:
        assert snapshot(reopened) == after
        assert DashboardRepository(reopened).get("b") == unchanged
        if fail:
            assert after == before
        else:
            assert DashboardRepository(reopened).get("a") == result
            assert result.created_at == "created" and result.updated_at != "before"
            assert result.sql_content == changes["sql_content"] and result.description is None
    finally:
        reopened.close()


def test_competing_parent_write_conflicts_but_unrelated_patch_commits(db):
    writer, competing = db.cursor(), db.cursor()
    try:
        with dashboard_write(writer, "a"):
            with pytest.raises(DashboardWriteConflict):
                DashboardRepository(competing).update("a", {"name": "Lost"})
            assert DashboardRepository(competing).get("a").name == "a"
            assert DashboardRepository(competing).update("b", {"name": "Independent"}).name == (
                "Independent"
            )
        assert DashboardRepository(competing).update("a", {"name": "Retry"}).name == "Retry"
    finally:
        writer.close()
        competing.close()


def test_reader_keeps_previous_snapshot_until_its_transaction_ends(db):
    writer, reader = db.cursor(), db.cursor()
    try:
        reader.begin()
        previous = DashboardRepository(reader).get("a")
        result = DashboardRepository(writer).update("a", {"name": "After", "description": None})
        assert DashboardRepository(reader).get("a") == previous
        reader.commit()
        assert DashboardRepository(reader).get("a") == result
    finally:
        writer.close()
        reader.close()


def test_deletion_between_read_and_update_cannot_return_a_ghost_result(db):
    writer, deleting = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)

    def execute(sql, parameters):
        if sql.startswith("UPDATE dashboards"):
            DashboardRepository(deleting).delete("a")
        return writer.execute(sql, parameters)

    proxy.execute.side_effect = execute
    try:
        with pytest.raises(DashboardWriteConflict):
            DashboardRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
                "a", {"name": "Lost"},
            )
        with pytest.raises(DashboardNotFound):
            DashboardRepository(db).get("a")
        assert DashboardRepository(db).get("b").name == "b"
    finally:
        writer.close()
        deleting.close()
