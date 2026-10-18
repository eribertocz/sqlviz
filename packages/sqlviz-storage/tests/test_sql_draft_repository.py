"""Draft versions, integration fences and rollback on real project cursors."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_core.models.sql_reconciliation import KeepSqlPanel
from sqlviz_core.models.sql_script import SqlScriptError, SqlStatement
from sqlviz_storage.dashboard_repository import DashboardNotFound, DashboardRepository
from sqlviz_storage.project_db import create_project, open_project
from sqlviz_storage.sql_draft_repository import SqlDraftRepository, SqlDraftWriteConflict
from sqlviz_storage.sql_draft_revision import (
    MAX_SQL_DRAFT_GENERATION,
    SqlDraftMetadataError,
    SqlDraftRevisionLimitError,
)
from sqlviz_storage.sql_script_repository import (
    SqlScriptRepository,
    SqlScriptWriteConflict,
    definition_revision,
)


def seed(db):
    for key in ("d", "other"):
        db.execute(
            "INSERT INTO dashboards (id, name, sql_content, created_at, updated_at, "
            "last_run_at, last_run_sql) VALUES (?, ?, 'SELECT 1', 't', 't', 'previous', 'old')",
            [key, key],
        )
    db.execute(
        "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at, "
        "view_title, col_span_user_override) "
        "VALUES ('p', 'd', 'P', 'SELECT 1', 't', 't', 'Title', 6)"
    )


@pytest.fixture
def db():
    conn = create_project(":memory:")
    seed(conn)
    try:
        yield conn
    finally:
        conn.close()


def state(db):
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("dashboards", "panels", "dashboard_sql_scripts", "_sqlviz_auth")}


def commit_same_sql(db):
    scripts = SqlScriptRepository(db)
    return scripts.write(
        "d", scripts.read("d").revision, "SELECT 1", [KeepSqlPanel(0, "p")],
        parse=lambda _: [SqlStatement("SELECT 1", 0, 8)],
    ).snapshot


@pytest.mark.parametrize("source", ["", "SELECT 'unfinished", "-- 🧠\r\nSELECT 'a;b';\n"])
def test_exact_unfinished_and_empty_drafts_do_not_change_definitions_or_last_run(db, source):
    confirmed = commit_same_sql(db)
    before = state(db)
    repo = SqlDraftRepository(db)
    previous = repo.read("d")
    saved = repo.write("d", previous.revision, source)
    assert saved.source == source and saved.generation == previous.generation + 1
    assert saved.initialized and saved.revision != previous.revision
    after = state(db)
    for table in ("panels", "dashboard_sql_scripts", "_sqlviz_auth"):
        assert after[table] == before[table]
    parent = DashboardRepository(db).get("d")
    assert parent.last_run_at == "previous" and parent.last_run_sql == "old"
    assert definition_revision(SqlScriptRepository(db).read("d")) == definition_revision(confirmed)
    assert DashboardRepository(db).get("other").sql_content == "SELECT 1"
    with pytest.raises(FrozenInstanceError):
        saved.source = "other"


def test_initial_empty_save_has_durable_provenance_and_stale_retry_cannot_write(db):
    db.execute("UPDATE dashboards SET sql_content = '' WHERE id = 'd'")
    repo = SqlDraftRepository(db)
    initial = repo.read("d")
    assert not initial.initialized and initial.generation == 0
    saved = repo.write("d", initial.revision, "")
    assert saved.initialized and saved.generation == 1
    before = state(db)
    with pytest.raises(SqlDraftWriteConflict):
        repo.write("d", initial.revision, "")
    assert state(db) == before


def test_legacy_writes_and_identical_run_commits_invalidate_captured_draft_tokens(db):
    repo = SqlDraftRepository(db)
    initial = repo.read("d")
    DashboardRepository(db).update("d", {"sql_content": "SELECT 1"})
    legacy = repo.read("d")
    assert legacy.revision != initial.revision
    commit_same_sql(db)
    committed = repo.read("d")
    assert committed.source == initial.source and committed.generation == 2
    before = state(db)
    for revision in (initial.revision, legacy.revision):
        with pytest.raises(SqlDraftWriteConflict):
            repo.write("d", revision, "late draft")
    assert state(db) == before


@pytest.mark.parametrize("legacy", [False, True])
def test_return_to_original_text_does_not_reuse_its_old_revision(db, legacy):
    repo = SqlDraftRepository(db)
    initial = repo.read("d")
    for source in ("SELECT 2", initial.source):
        if legacy:
            DashboardRepository(db).update("d", {"sql_content": source})
        else:
            repo.write("d", repo.read("d").revision, source)
    assert repo.read("d").source == initial.source
    with pytest.raises(SqlDraftWriteConflict):
        repo.write("d", initial.revision, "late draft")


def test_presentation_inference_and_last_run_changes_do_not_make_a_draft_stale(db):
    repo = SqlDraftRepository(db)
    initial = repo.read("d")
    DashboardRepository(db).update("d", {"name": "Renamed", "description": "Description"})
    db.execute("UPDATE panels SET inferred_chart_type = 'bar', view_title = 'Changed'")
    db.execute(
        "UPDATE dashboards SET last_run_at = 'new', last_run_sql = 'confirmed' WHERE id = 'd'"
    )
    assert repo.read("d") == initial
    repo.write("d", initial.revision, "unfinished")
    parent = DashboardRepository(db).get("d")
    assert (parent.name, parent.description, parent.last_run_at, parent.last_run_sql) == (
        "Renamed", "Description", "new", "confirmed",
    )


def test_token_belongs_to_its_dashboard_and_read_is_not_a_write(db):
    repo = SqlDraftRepository(db)
    before = state(db)
    a, b = repo.read("d"), repo.read("other")
    assert a.source == b.source and a.generation == b.generation
    assert a.revision != b.revision and state(db) == before
    with pytest.raises(SqlDraftWriteConflict):
        repo.write("other", a.revision, "wrong owner")
    with pytest.raises(DashboardNotFound):
        repo.read("missing")
    with pytest.raises(DashboardNotFound):
        repo.write("missing", a.revision, "draft")
    assert state(db) == before


@pytest.mark.parametrize("source", ["\x00tail", "\ud800", "x" * (1024 * 1024 + 1)],
                         ids=["nul", "surrogate", "byte-limit"])
def test_invalid_text_or_byte_budget_rejected_before_writes(db, source):
    repo = SqlDraftRepository(db)
    before = state(db)
    with pytest.raises(SqlScriptError):
        repo.write("d", repo.read("d").revision, source)
    assert state(db) == before


@pytest.mark.parametrize("revision", [None, True, "bad", "sql-draft-v1:" + "G" * 64,
                                      "sql-draft-v1:" + "a" * 64 + "\n"])
def test_malformed_revision_cannot_mutate_draft(db, revision):
    before = state(db)
    with pytest.raises(ValueError):
        SqlDraftRepository(db).write("d", revision, "draft")
    assert state(db) == before


@pytest.mark.parametrize("racing", ["draft", "legacy", "run", "rename", "delete"])
def test_competing_write_after_snapshot_rolls_back_draft_and_keeps_winner(db, racing):
    initial = SqlDraftRepository(db).read("d")
    proxy = Mock(wraps=db)
    raced = False

    def execute(sql, parameters):
        nonlocal raced
        if sql.startswith("UPDATE dashboards") and not raced:
            raced = True
            with db.cursor() as competing:
                if racing == "draft":
                    SqlDraftRepository(competing).write("d", initial.revision, "winning draft")
                elif racing == "legacy":
                    DashboardRepository(competing).update("d", {"sql_content": "winning draft"})
                elif racing == "run":
                    commit_same_sql(competing)
                elif racing == "rename":
                    DashboardRepository(competing).update("d", {"name": "Winner"})
                else:
                    DashboardRepository(competing).delete("d")
        return db.execute(sql, parameters)

    proxy.execute.side_effect = execute
    with pytest.raises(SqlDraftWriteConflict):
        SqlDraftRepository(cast(duckdb.DuckDBPyConnection, proxy)).write(
            "d", initial.revision, "losing draft",
        )
    assert raced
    if racing == "delete":
        with pytest.raises(DashboardNotFound):
            SqlDraftRepository(db).read("d")
        assert db.execute("SELECT count(*) FROM panels WHERE dashboard_id = 'd'").fetchone() == (0,)
    else:
        saved = SqlDraftRepository(db).read("d")
        assert saved.source == ("winning draft" if racing in ("draft", "legacy") else "SELECT 1")
        assert saved.generation == (0 if racing == "rename" else 1)
        if racing == "rename":
            assert DashboardRepository(db).get("d").name == "Winner"


def test_draft_save_invalidates_full_script_commit_token_even_for_identical_text(db):
    scripts = SqlScriptRepository(db)
    before = scripts.read("d")
    repo = SqlDraftRepository(db)
    repo.write("d", repo.read("d").revision, "SELECT 1")
    with pytest.raises(SqlScriptWriteConflict):
        scripts.write("d", before.revision, "SELECT 1", [KeepSqlPanel(0, "p")],
                      parse=lambda _: [SqlStatement("SELECT 1", 0, 8)])
    assert scripts.read("d").publication is None


@pytest.mark.parametrize("competing", ["draft", "legacy", "run", "delete"])
def test_parent_fence_is_held_until_draft_commit(db, competing):
    from sqlviz_storage.dashboard_repository import DashboardWriteConflict

    initial = SqlDraftRepository(db).read("d")
    proxy = Mock(wraps=db)

    def commit():
        with db.cursor() as other:
            if competing == "draft":
                with pytest.raises(SqlDraftWriteConflict):
                    SqlDraftRepository(other).write("d", initial.revision, "loser")
            elif competing == "legacy":
                with pytest.raises(DashboardWriteConflict):
                    DashboardRepository(other).update("d", {"sql_content": "loser"})
            elif competing == "run":
                with pytest.raises(SqlScriptWriteConflict):
                    commit_same_sql(other)
            else:
                with pytest.raises(DashboardWriteConflict):
                    DashboardRepository(other).delete("d")
            # Unrelated aggregate remains independently writable.
            other_drafts = SqlDraftRepository(other)
            other_drafts.write("other", other_drafts.read("other").revision, "independent")
        db.commit()

    proxy.commit.side_effect = commit
    saved = SqlDraftRepository(cast(duckdb.DuckDBPyConnection, proxy)).write(
        "d", initial.revision, "winner",
    )
    assert SqlDraftRepository(db).read("d") == saved and saved.source == "winner"
    assert SqlDraftRepository(db).read("other").source == "independent"
    assert SqlScriptRepository(db).read("d").publication is None


def test_nullable_legacy_source_can_be_saved_without_guessing_a_generation(db):
    db.execute("UPDATE dashboards SET sql_content = NULL WHERE id = 'd'")
    repo = SqlDraftRepository(db)
    initial = repo.read("d")
    assert initial.source == "" and initial.generation == 0 and not initial.initialized
    assert repo.write("d", initial.revision, "unfinished").generation == 1


@pytest.mark.parametrize("generation", [-1, MAX_SQL_DRAFT_GENERATION])
def test_invalid_or_exhausted_generation_never_resets_or_partially_writes(db, generation):
    db.execute("UPDATE dashboards SET sql_draft_generation = ? WHERE id = 'd'", [generation])
    before = state(db)
    error = SqlDraftMetadataError if generation < 0 else SqlDraftRevisionLimitError
    with pytest.raises(error):
        repo = SqlDraftRepository(db)
        repo.write("d", repo.read("d").revision, "draft")
    with pytest.raises(error):
        DashboardRepository(db).update("d", {"name": "Must roll back", "sql_content": "draft"})
    with pytest.raises(error):
        commit_same_sql(db)
    assert state(db) == before


@pytest.mark.parametrize("failure", ["read", "commit"])
def test_failed_write_rolls_back_source_generation_and_timestamp_on_reopen(tmp_path, failure):
    path = str(tmp_path / "draft.sqlviz")
    db = create_project(path)
    seed(db)
    before = state(db)
    initial = SqlDraftRepository(db).read("d")
    proxy = Mock(wraps=db)
    wrote = False

    def execute(sql, parameters):
        nonlocal wrote
        if wrote and sql.startswith("SELECT sql_content") and failure == "read":
            raise RuntimeError("synthetic read failure")
        if sql.startswith("UPDATE dashboards SET sql_content"):
            wrote = True
        return db.execute(sql, parameters)

    proxy.execute.side_effect = execute
    if failure == "commit":
        proxy.commit.side_effect = duckdb.TransactionException("synthetic commit failure")
    try:
        with pytest.raises(SqlDraftWriteConflict if failure == "commit" else RuntimeError):
            SqlDraftRepository(cast(duckdb.DuckDBPyConnection, proxy)).write(
                "d", initial.revision, "unfinished",
            )
        assert state(db) == before
    finally:
        db.close()
    reopened = open_project(path)
    try:
        assert state(reopened) == before
        assert SqlDraftRepository(reopened).read("d") == initial
    finally:
        reopened.close()
