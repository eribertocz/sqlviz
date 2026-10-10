"""Completion fences real peer writers and rolls back every own mutation."""

from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_core.models.sql_reconciliation import KeepSqlPanel
from sqlviz_core.models.sql_script import SqlStatement
from sqlviz_storage.panel_repository import PanelRepository
from sqlviz_storage.project_db import create_project
from sqlviz_storage.sql_run_completion import record_sql_run
from sqlviz_storage.sql_script_repository import (
    SqlDefinitionConflict,
    SqlDefinitionReference,
    SqlScriptRepository,
    definition_revision,
)

SOURCE = "SELECT 1; SELECT 2"
STATEMENTS = (SqlStatement("SELECT 1", 0, 8), SqlStatement("SELECT 2", 10, 18))
CHOICES = (KeepSqlPanel(0, "a"), KeepSqlPanel(1, "b"))
COMPLETED = "2026-10-09T17:00:00.123456+00:00"


@pytest.fixture
def db():
    conn = create_project(":memory:")
    conn.execute(
        "INSERT INTO dashboards (id, name, created_at, updated_at) VALUES ('d', 'D', 't', 't')"
    )
    for panel, sql in (("a", "SELECT 1"), ("b", "SELECT 2")):
        conn.execute(
            "INSERT INTO panels (id, dashboard_id, name, sql_content, "
            "created_at, updated_at) VALUES (?, 'd', ?, ?, 't', 't')",
            [panel, panel, sql],
        )
    repository = SqlScriptRepository(conn)
    repository.write(
        "d", repository.read("d").revision, SOURCE, CHOICES, parse=lambda _: STATEMENTS
    )
    yield conn
    conn.close()


def reference(db):
    return SqlDefinitionReference("d", definition_revision(SqlScriptRepository(db).read("d")))


def state(db):
    return {
        table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        for table in ("dashboards", "panels", "dashboard_sql_scripts")
    }


@pytest.mark.parametrize("mutation", ["sql", "delete"])
def test_peer_change_committed_after_snapshot_read_rolls_back_acknowledgement(
    db, monkeypatch, mutation
):
    wanted = reference(db)
    writer, competing = db.cursor(), db.cursor()
    original = SqlScriptRepository.require_definition

    def racing(repository, expected):
        snapshot = original(repository, expected)
        if mutation == "sql":
            PanelRepository(competing).update("b", {"sql_content": "SELECT 99"})
        else:
            PanelRepository(competing).delete("b")
        return snapshot

    monkeypatch.setattr(SqlScriptRepository, "require_definition", racing)
    parent_before = db.execute("SELECT * FROM dashboards WHERE id = 'd'").fetchone()
    own_before = PanelRepository(db).get("a")
    try:
        with pytest.raises(SqlDefinitionConflict):
            record_sql_run(writer, wanted, COMPLETED)
        assert db.execute("SELECT * FROM dashboards WHERE id = 'd'").fetchone() == parent_before
        assert PanelRepository(db).get("a") == own_before
        if mutation == "sql":
            assert PanelRepository(db).get("b").sql_content == "SELECT 99"
        else:
            assert db.execute("SELECT id FROM panels WHERE id = 'b'").fetchone() is None
    finally:
        writer.close()
        competing.close()


def test_failed_commit_rolls_back_timestamps_and_both_success_fields(db):
    wanted = reference(db)
    before = state(db)
    writer = db.cursor()
    proxy = Mock(wraps=writer)
    proxy.commit.side_effect = duckdb.TransactionException("synthetic commit conflict")
    try:
        with pytest.raises(SqlDefinitionConflict):
            record_sql_run(proxy, wanted, COMPLETED)
        assert state(db) == before
    finally:
        writer.close()


def test_trusted_writer_never_uses_a_newer_draft_as_the_executed_source(db):
    wanted = reference(db)
    db.execute("UPDATE dashboards SET sql_content = 'SELECT new_draft' WHERE id = 'd'")
    result = record_sql_run(db, wanted, COMPLETED)
    assert result.last_run_sql == SOURCE
    assert db.execute(
        "SELECT sql_content, last_run_sql, last_run_at FROM dashboards"
    ).fetchone() == (
        "SELECT new_draft",
        SOURCE,
        COMPLETED,
    )
