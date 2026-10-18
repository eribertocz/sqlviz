"""Atomic folder changes and real competing DuckDB transactions."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_core.models.folders import FolderError
from sqlviz_storage.folder_repository import (
    FOLDER_TREE_REVISION_KEY,
    FolderRepository,
    FolderWriteConflict,
    folder_tree_write,
)
from sqlviz_storage.project_db import create_project, open_project


@pytest.fixture
def db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    conn = create_project(":memory:")
    yield conn
    conn.close()


def snapshot(db) -> dict:
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("folders", "dashboards", "panels", "shares", "_sqlviz_meta")}


def test_create_move_omit_detach_preserve_identity(db) -> None:
    repo = FolderRepository(db)
    a, b = repo.create("A"), repo.create("B")
    child = repo.create("Child", a.id)
    renamed = repo.update(child.id, {"name": "Renamed", "sort_order": 7})
    assert renamed.parent_id == a.id
    assert repo.update(child.id, {"parent_id": b.id}).parent_id == b.id
    detached = repo.update(child.id, {"parent_id": None})
    assert detached.parent_id is None and detached.name == "Renamed" and detached.sort_order == 7
    assert detached.id == child.id and detached.created_at == child.created_at
    before = snapshot(db)
    assert repo.update(child.id, {}) == detached
    assert snapshot(db) == before


@pytest.mark.parametrize("operation", ["create", "update"])
def test_missing_destination_leaves_rows_and_revision_unchanged(db, operation) -> None:
    repo = FolderRepository(db)
    a = repo.create("A")
    before = snapshot(db)
    with pytest.raises(FolderError) as error:
        if operation == "create":
            repo.create("Bad", "missing")
        else:
            repo.update(a.id, {"parent_id": "missing", "name": "Must roll back"})
    assert error.value.code == "folder_parent_not_found"
    assert snapshot(db) == before


@pytest.mark.parametrize("depth", [0, 1, 4])
def test_cycle_rejection_is_atomic(db, depth) -> None:
    repo = FolderRepository(db)
    root = repo.create("Root")
    descendant = root
    for i in range(depth):
        descendant = repo.create(f"Child {i}", descendant.id)
    before = snapshot(db)
    with pytest.raises(FolderError) as error:
        repo.update(root.id, {"parent_id": descendant.id, "name": "Changed"})
    assert error.value.code == "folder_cycle"
    assert snapshot(db) == before


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_missing_resource_does_not_commit_a_revision(db, operation) -> None:
    repo = FolderRepository(db)
    before = snapshot(db)
    with pytest.raises(FolderError) as error:
        if operation == "update":
            repo.update("missing", {"name": "Changed"})
        else:
            getattr(repo, operation)("missing")
    assert error.value.code == "folder_not_found"
    assert snapshot(db) == before


def seed_contents(db, repo):
    parent = repo.create("Parent")
    child = repo.create("Child", parent.id)
    grandchild = repo.create("Grandchild", child.id)
    other = repo.create("Other")
    db.execute("INSERT INTO dashboards (id, name, folder_id, created_at, updated_at) "
               "VALUES ('dash', 'Dash', ?, 't', 't')", [parent.id])
    db.execute("INSERT INTO panels (id, dashboard_id, name, created_at, updated_at) "
               "VALUES ('panel', 'dash', 'Panel', 't', 't')")
    db.execute("INSERT INTO shares VALUES ('share', 'dash', 'nonce', 'token', 'public', "
               "NULL, 't', false)")
    return parent, child, grandchild, other


def test_delete_promotes_direct_contents_and_preserves_subtrees_and_dashboard_data(db) -> None:
    repo = FolderRepository(db)
    parent, child, grandchild, other = seed_contents(db, repo)
    before = snapshot(db)
    repo.delete(parent.id)
    assert repo.get(child.id).parent_id is None
    assert repo.get(grandchild.id).parent_id == child.id
    assert repo.get(other.id) == other
    assert db.execute("SELECT folder_id FROM dashboards WHERE id = 'dash'").fetchone() == (None,)
    assert snapshot(db)["panels"] == before["panels"]
    assert snapshot(db)["shares"] == before["shares"]
    with pytest.raises(FolderError):
        repo.get(parent.id)


@pytest.mark.parametrize("failure_stage", ["children", "parent", "commit"])
def test_failure_after_dashboard_promotion_rolls_back_everything(db, failure_stage) -> None:
    repo = FolderRepository(db)
    parent, _, _, _ = seed_contents(db, repo)
    before = snapshot(db)
    cursor = Mock(wraps=db)
    original_execute = db.execute

    def execute(sql, parameters=None):
        fails = (
            failure_stage == "children" and sql.startswith("UPDATE folders SET parent_id")
        ) or (failure_stage == "parent" and sql.startswith("DELETE FROM folders"))
        if fails:
            raise RuntimeError("synthetic database failure")
        return original_execute(sql, parameters)

    cursor.execute.side_effect = execute
    if failure_stage == "commit":
        cursor.commit.side_effect = duckdb.TransactionException("synthetic commit conflict")
    expected = FolderWriteConflict if failure_stage == "commit" else RuntimeError
    with pytest.raises(expected):
        FolderRepository(cast(duckdb.DuckDBPyConnection, cursor)).delete(parent.id)
    assert snapshot(db) == before
    repo.delete(parent.id)  # The cursor/transaction remains usable.


def test_real_fk_failure_rolls_back_promotions(db) -> None:
    repo = FolderRepository(db)
    parent, _, _, _ = seed_contents(db, repo)
    db.execute("CREATE TABLE retained (folder_id VARCHAR REFERENCES folders(id))")
    db.execute("INSERT INTO retained VALUES (?)", [parent.id])
    before = snapshot(db)
    with pytest.raises(FolderWriteConflict):
        repo.delete(parent.id)
    assert snapshot(db) == before


def test_opposite_concurrent_moves_cannot_create_cycle(db) -> None:
    repo = FolderRepository(db)
    a, b = repo.create("A"), repo.create("B")
    moving, competing = db.cursor(), db.cursor()
    try:
        with folder_tree_write(moving):
            moving.execute("UPDATE folders SET parent_id = ? WHERE id = ?", [b.id, a.id])
            with pytest.raises(FolderWriteConflict):
                FolderRepository(competing).update(b.id, {"parent_id": a.id})
        with pytest.raises(FolderError) as error:
            FolderRepository(competing).update(b.id, {"parent_id": a.id})
        assert error.value.code == "folder_cycle"
        assert repo.get(a.id).parent_id == b.id and repo.get(b.id).parent_id is None
    finally:
        moving.close()
        competing.close()


def test_child_created_before_delete_conflicts_then_is_promoted_on_retry(db) -> None:
    repo = FolderRepository(db)
    parent = repo.create("Parent")
    creating, deleting = db.cursor(), db.cursor()
    try:
        with folder_tree_write(creating):
            creating.execute(
                "INSERT INTO folders VALUES ('child', 'Child', ?, 0, 't')", [parent.id],
            )
            with pytest.raises(FolderWriteConflict):
                FolderRepository(deleting).delete(parent.id)
        assert repo.get("child").parent_id == parent.id
        FolderRepository(deleting).delete(parent.id)
        assert repo.get("child").parent_id is None
    finally:
        creating.close()
        deleting.close()


def test_corrupt_revision_is_explicit_and_never_resets_metadata(db) -> None:
    repo = FolderRepository(db)
    folder = repo.create("Keep")
    db.execute(
        "UPDATE _sqlviz_meta SET value = 'invalid' WHERE key = ?", [FOLDER_TREE_REVISION_KEY],
    )
    before = snapshot(db)
    with pytest.raises(FolderError) as error:
        repo.update(folder.id, {"name": "Changed"})
    assert error.value.code == "folder_hierarchy_invalid"
    assert snapshot(db) == before


def test_first_writers_on_legacy_file_conflict_at_commit_without_masking_original_error(db) -> None:
    # Historical projects have folders but no revision key. Two first writers
    # insert the same key; only one may commit, even when each move alone is valid.
    db.execute("INSERT INTO folders VALUES ('a', 'A', NULL, 0, 't'), ('b', 'B', NULL, 0, 't')")
    first, second = db.cursor(), db.cursor()
    try:
        with pytest.raises(FolderWriteConflict):
            with folder_tree_write(first):
                first.execute("UPDATE folders SET parent_id = 'b' WHERE id = 'a'")
                FolderRepository(second).update("b", {"parent_id": "a"})
        repo = FolderRepository(db)
        assert repo.get("a").parent_id is None and repo.get("b").parent_id == "a"
        assert db.execute("SELECT value FROM _sqlviz_meta WHERE key = ?",
                          [FOLDER_TREE_REVISION_KEY]).fetchone() == ("1",)
        assert FolderRepository(first).create("Recovered").name == "Recovered"
    finally:
        first.close()
        second.close()


@pytest.mark.parametrize("operation", ["create_child", "move_child", "assign_dashboard"])
def test_destination_deletion_conflicts_with_dependent_writes(db, operation) -> None:
    repo = FolderRepository(db)
    parent, child = repo.create("Parent"), repo.create("Child")
    deleting, creating = db.cursor(), db.cursor()

    def write():
        target = FolderRepository(creating)
        if operation == "create_child":
            target.create("New", parent.id)
        elif operation == "move_child":
            target.update(child.id, {"parent_id": parent.id})
        else:
            with target.dashboard_placement(parent.id):
                creating.execute("INSERT INTO dashboards (id,name,folder_id,created_at,updated_at) "
                                 "VALUES ('new','New',?,'t','t')", [parent.id])

    try:
        with folder_tree_write(deleting):
            deleting.execute("DELETE FROM folders WHERE id = ?", [parent.id])
            with pytest.raises(FolderWriteConflict):
                write()
        before = snapshot(db)
        with pytest.raises(FolderError) as error:
            write()
        assert error.value.code == "folder_parent_not_found"
        assert snapshot(db) == before
    finally:
        deleting.close()
        creating.close()


@pytest.mark.parametrize("fail", [False, True])
def test_reopen_after_delete_or_rollback_preserves_complete_state(tmp_path: Path, fail) -> None:
    path = tmp_path / "folders.sqlviz"
    conn = create_project(str(path))
    try:
        repo = FolderRepository(conn)
        parent, _, _, _ = seed_contents(conn, repo)
        if fail:
            conn.execute("CREATE TABLE retained (folder_id VARCHAR REFERENCES folders(id))")
            conn.execute("INSERT INTO retained VALUES (?)", [parent.id])
        if fail:
            with pytest.raises(FolderWriteConflict):
                repo.delete(parent.id)
        else:
            repo.delete(parent.id)
        after = snapshot(conn)
    finally:
        conn.close()
    reopened = open_project(str(path))
    try:
        assert snapshot(reopened) == after
    finally:
        reopened.close()
