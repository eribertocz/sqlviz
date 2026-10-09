"""Rollback, optimistic state and competing writers on real DuckDB cursors.

Parser fixtures supply explicit native-style slices; native parser integration
is tested separately in the API package, which owns that service.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_core.models.sql_reconciliation import (
    CreateSqlPanel,
    KeepSqlPanel,
    RemoveSqlPanel,
    SqlReconciliationError,
)
from sqlviz_core.models.sql_script import SqlStatement
from sqlviz_storage.dashboard_repository import (
    DashboardNotFound,
    DashboardRepository,
    DashboardWriteConflict,
    dashboard_write,
)
from sqlviz_storage.panel_repository import PanelRepository, PanelWriteConflict
from sqlviz_storage.project_db import create_project, open_project
from sqlviz_storage.sql_script_repository import (
    SqlScriptMetadataError,
    SqlScriptRepository,
    SqlScriptWriteConflict,
)


def seed(db):
    for dashboard in ("d", "other"):
        db.execute(
            "INSERT INTO dashboards (id, name, created_at, updated_at, last_run_sql) "
            "VALUES (?, ?, 't', 't', 'successful previous run')",
            [dashboard, dashboard],
        )
    for panel, owner, sql in [
        ("a", "d", "SELECT 1"),
        ("b", "d", "SELECT 2"),
        ("z", "other", "SELECT 9"),
    ]:
        db.execute(
            "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 't', 't')",
            [panel, owner, panel.upper(), sql],
        )
    db.execute(
        "UPDATE panels SET col_span_user_override = 6, selected_col_span = 6, "
        "chart_user_override = 'bar', selected_chart_type = 'bar', "
        "height_user_override = 320, selected_height_px = 320, "
        "view_title = 'Revenue', view_x_label = 'Region', view_y_label = 'USD', "
        "fingerprint = 'old', inferred_chart_type = 'line', inferred_col_span = 12, "
        "inferred_height_px = 250, inferred_intent_type = 'old' WHERE id = 'b'"
    )
    db.execute(
        "INSERT INTO shares VALUES ('share', 'd', 'nonce', 'token', 'public', NULL, 't', false)"
    )
    db.execute("INSERT INTO filter_memory VALUES ('d', 'region', 'North', 't')")
    db.execute("CREATE TABLE sales (amount INTEGER)")
    db.execute("INSERT INTO sales VALUES (42)")


@pytest.fixture
def db():
    conn = create_project(":memory:")
    seed(conn)
    yield conn
    conn.close()


def rows(db):
    return {
        table: db.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall()
        for table in (
            "dashboards",
            "panels",
            "dashboard_sql_scripts",
            "shares",
            "filter_memory",
            "_sqlviz_auth",
            "sales",
        )
    }


def parser(source, sqls):
    """Known fixture queries, including semicolons in literals; no SQL splitting."""
    statements = []
    offset = 0
    for sql in sqls:
        start = source.index(sql, offset)
        offset = start + len(sql)
        statements.append(
            SqlStatement(
                sql,
                len(source[:start].encode("utf-16-le")) // 2,
                len(source[:offset].encode("utf-16-le")) // 2,
            )
        )
    return Mock(return_value=tuple(statements))


def write(
    repo,
    *,
    expected=None,
    source="SELECT 22; SELECT 3",
    sqls=("SELECT 22", "SELECT 3"),
    choices=None,
    dashboard="d",
):
    if expected is None:
        expected = repo.read(dashboard).revision
    if choices is None:
        choices = [KeepSqlPanel(0, "b"), CreateSqlPanel(1, "new"), RemoveSqlPanel("a")]
    return repo.write(dashboard, expected, source, choices, parse=parser(source, sqls))


def test_batch_keeps_manual_settings_allocates_new_ids_and_removes_only_explicit_refs(db):
    repo = SqlScriptRepository(db)
    before = rows(db)
    result = write(repo)
    snapshot = result.snapshot
    assert repo.read("d") == snapshot
    assert snapshot.publication.revision == 1
    assert snapshot.draft_source == "SELECT 22; SELECT 3"
    new_id = result.created_panels[0][1]
    assert result.created_panels == (("new", new_id),) and new_id not in {"a", "b", "new"}
    assert [binding.panel_id for binding in snapshot.publication.bindings] == ["b", new_id]
    retained = PanelRepository(db).get("b")
    assert retained.sql_content == "SELECT 22" and retained.sort_order == 0 and retained.name == "B"
    assert (
        retained.col_span_user_override,
        retained.height_user_override,
        retained.chart_user_override,
    ) == (6, 320, "bar")
    assert (retained.view_title, retained.view_x_label, retained.view_y_label) == (
        "Revenue",
        "Region",
        "USD",
    )
    assert retained.fingerprint is None and retained.inferred_chart_type is None
    assert retained.selected_chart_type == "bar" and retained.selected_col_span == 6
    assert db.execute("SELECT inferred_intent_type FROM panels WHERE id = 'b'").fetchone() == (
        None,
    )
    assert db.execute("SELECT id FROM panels ORDER BY id").fetchall() == sorted(
        [("b",), (new_id,), ("z",)]
    )
    after = rows(db)
    for table in ("shares", "filter_memory", "_sqlviz_auth", "sales"):
        assert after[table] == before[table]
    assert DashboardRepository(db).get("d").last_run_sql == "successful previous run"
    assert DashboardRepository(db).get("other").updated_at == "t"


def test_reorder_with_unchanged_sql_keeps_inference_and_binds_by_id(db):
    repo = SqlScriptRepository(db)
    result = write(
        repo,
        source="SELECT 2; SELECT 1",
        sqls=("SELECT 2", "SELECT 1"),
        choices=[KeepSqlPanel(0, "b"), KeepSqlPanel(1, "a")],
    )
    assert [binding.panel_id for binding in result.snapshot.publication.bindings] == ["b", "a"]
    assert PanelRepository(db).get("b").fingerprint == "old"
    assert PanelRepository(db).get("a").sort_order == 1


@pytest.mark.parametrize(
    "mutation",
    ["sql", "order", "override", "title", "draft", "name", "add", "delete", "raw_sql", "intent"],
)
def test_every_stale_expected_state_rejects_the_whole_batch(db, mutation):
    repo = SqlScriptRepository(db)
    expected = repo.read("d").revision
    panels = PanelRepository(db)
    if mutation == "sql":
        panels.update("a", {"sql_content": "SELECT 99"})
    elif mutation == "order":
        panels.update("a", {"sort_order": 10})
    elif mutation == "override":
        panels.set_override("a", "col_span", "8")
    elif mutation == "title":
        panels.set_presentation("a", "title", "Changed")
    elif mutation == "draft":
        DashboardRepository(db).update("d", {"sql_content": "SELECT 44"})
    elif mutation == "name":
        DashboardRepository(db).update("d", {"name": "Renamed"})
    elif mutation == "delete":
        panels.delete("a")
    elif mutation == "add":
        with dashboard_write(db, "d"):
            db.execute(
                "INSERT INTO panels (id, dashboard_id, name, created_at, updated_at) "
                "VALUES ('extra', 'd', 'Extra', 't', 't')"
            )
    elif mutation == "intent":
        db.execute("UPDATE panels SET inferred_intent_type = 'changed' WHERE id = 'a'")
    else:
        db.execute("UPDATE panels SET sql_content = 'SELECT 33' WHERE id = 'a'")
    before = rows(db)
    with pytest.raises(SqlScriptWriteConflict):
        write(repo, expected=expected)
    assert rows(db) == before


@pytest.mark.parametrize(
    "choices", [[], [KeepSqlPanel(0, "z")], [KeepSqlPanel(0, "b"), KeepSqlPanel(1, "b")]]
)
def test_incomplete_foreign_and_duplicate_decisions_never_mutate(db, choices):
    repo = SqlScriptRepository(db)
    before = rows(db)
    with pytest.raises(SqlReconciliationError):
        write(repo, choices=choices)
    assert rows(db) == before


@pytest.mark.parametrize(
    "stage",
    [
        "UPDATE panels",
        "INSERT INTO panels",
        "DELETE FROM panels",
        "INSERT INTO dashboard_sql_scripts",
        "commit",
    ],
)
def test_failures_at_every_write_stage_restore_the_whole_previous_state(db, stage):
    before = rows(db)
    proxy = Mock(wraps=db)
    if stage == "commit":
        proxy.commit.side_effect = duckdb.TransactionException("commit failed")
    else:

        def execute(sql, *args):
            if sql.startswith(stage):
                raise duckdb.CatalogException("stage failed")
            return db.execute(sql, *args)

        proxy.execute.side_effect = execute
    repo = SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy))
    error = SqlScriptWriteConflict if stage == "commit" else duckdb.CatalogException
    with pytest.raises(error):
        write(repo, expected=SqlScriptRepository(db).read("d").revision)
    assert rows(db) == before
    assert write(SqlScriptRepository(db)).snapshot.publication.revision == 1


def test_commit_failure_also_restores_an_existing_publication(db):
    repo = SqlScriptRepository(db)
    write(
        repo,
        source="SELECT 2; SELECT 1",
        sqls=("SELECT 2", "SELECT 1"),
        choices=[KeepSqlPanel(0, "b"), KeepSqlPanel(1, "a")],
    )
    before = rows(db)
    proxy = Mock(wraps=db)
    proxy.commit.side_effect = duckdb.TransactionException("commit failed")
    with pytest.raises(SqlScriptWriteConflict):
        write(
            SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy)),
            expected=repo.read("d").revision,
        )
    assert rows(db) == before


def test_exact_stale_retry_cannot_duplicate_a_creation(db):
    repo = SqlScriptRepository(db)
    expected = repo.read("d").revision
    result = write(repo, expected=expected)
    before = rows(db)
    with pytest.raises(SqlScriptWriteConflict):
        write(repo, expected=expected)
    assert rows(db) == before
    assert result.snapshot.revision != expected


def test_empty_script_requires_explicit_removals_and_persists_empty_identity(db):
    repo = SqlScriptRepository(db)
    result = write(
        repo,
        source="-- intentionally empty;",
        sqls=(),
        choices=[RemoveSqlPanel("a"), RemoveSqlPanel("b")],
    )
    assert result.snapshot.panels == () and result.snapshot.publication.bindings == ()
    assert result.snapshot.draft_source == "-- intentionally empty;"
    assert PanelRepository(db).get("z").sql_content == "SELECT 9"


def test_document_is_durable_utf16_and_duplicate_sql_never_matches_by_content(tmp_path):
    path = str(tmp_path / "copy.sqlviz")
    db = create_project(path)
    seed(db)
    try:
        PanelRepository(db).update("a", {"sql_content": "SELECT '😀;x'"})
        PanelRepository(db).update("b", {"sql_content": "SELECT '😀;x'"})
        source = "SELECT '😀;x';\nSELECT '😀;x'"
        result = write(
            SqlScriptRepository(db),
            source=source,
            sqls=("SELECT '😀;x'", "SELECT '😀;x'"),
            choices=[KeepSqlPanel(0, "b"), KeepSqlPanel(1, "a")],
        )
    finally:
        db.close()
    reopened = open_project(path)
    try:
        assert SqlScriptRepository(reopened).read("d") == result.snapshot
        assert result.snapshot.publication.bindings[1].start_offset == 15
    finally:
        reopened.close()


def test_legacy_edits_invalidate_stored_associations_but_overrides_do_not(db):
    repo = SqlScriptRepository(db)
    write(repo)
    initial = repo.read("d")
    PanelRepository(db).set_presentation("b", "title", "New title")
    changed = repo.read("d")
    assert changed.publication == initial.publication and changed.revision != initial.revision
    PanelRepository(db).update("b", {"sql_content": "SELECT 44"})
    assert repo.read("d").publication is None
    assert db.execute("SELECT count(*) FROM dashboard_sql_scripts").fetchone() == (1,)
    new_id = initial.publication.bindings[1].panel_id
    assert (
        write(
            repo, choices=[KeepSqlPanel(0, "b"), KeepSqlPanel(1, new_id)]
        ).snapshot.publication.revision
        == 2
    )


@pytest.mark.parametrize(
    "document",
    [
        "{",
        '{"version":true,"bindings":[]}',
        '{"version":2,"bindings":[]}',
        '{"version":2,"version":1,"bindings":[]}',
        '{"version":1,"bindings":[{"panel_id":"b","start_offset":true,"end_offset":9}]}',
        '{"version":1,"bindings":[{"panel_id":"b","start_offset":-1,"end_offset":9}]}',
    ],
)
def test_corrupt_metadata_is_never_used_as_identity(db, document):
    repo = SqlScriptRepository(db)
    write(repo)
    db.execute("UPDATE dashboard_sql_scripts SET bindings_json = ?", [document])
    before = rows(db)
    with pytest.raises(SqlScriptMetadataError):
        repo.read("d")
    assert rows(db) == before


def test_publication_revision_advances_even_with_a_repeated_clock(db, monkeypatch):
    import sqlviz_storage.sql_script_repository as module

    monkeypatch.setattr(module, "modification_timestamp", lambda _previous: "fixed")
    repo = SqlScriptRepository(db)
    kwargs = dict(
        source="SELECT 2; SELECT 1",
        sqls=("SELECT 2", "SELECT 1"),
        choices=[KeepSqlPanel(0, "b"), KeepSqlPanel(1, "a")],
    )
    first = write(repo, **kwargs).snapshot
    second = write(repo, **kwargs).snapshot
    third = write(repo, **kwargs).snapshot
    assert [item.publication.revision for item in (first, second, third)] == [1, 2, 3]
    assert len({item.revision for item in (first, second, third)}) == 3


def test_snapshot_is_immutable_and_missing_dashboard_is_not_created(db):
    repo = SqlScriptRepository(db)
    snapshot = repo.read("d")
    assert snapshot.publication is None
    with pytest.raises(FrozenInstanceError):
        snapshot.draft_source = "Changed"
    with pytest.raises(DashboardNotFound):
        repo.read("missing")
    assert rows(db)["dashboard_sql_scripts"] == []


def test_reader_sees_previous_complete_snapshot_until_commit(db):
    writer, reader = db.cursor(), db.cursor()
    repo = SqlScriptRepository(reader)
    before = repo.read("d")
    proxy = Mock(wraps=writer)

    def commit():
        assert repo.read("d") == before
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        result = write(SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy)))
        assert repo.read("d") == result.snapshot
    finally:
        writer.close()
        reader.close()


@pytest.mark.parametrize("operation", ["patch", "override", "delete", "create", "dashboard_delete"])
def test_batch_fences_all_owned_rows_against_competing_legacy_operations(db, operation):
    writer, competing = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)

    def commit():
        with pytest.raises((PanelWriteConflict, DashboardWriteConflict)):
            panels = PanelRepository(competing)
            if operation == "patch":
                panels.update("b", {"name": "Competing"})
            elif operation == "override":
                panels.set_override("b", "col_span", "8")
            elif operation == "delete":
                panels.delete("a")
            elif operation == "dashboard_delete":
                DashboardRepository(competing).delete("d")
            else:
                with dashboard_write(competing, "d"):
                    competing.execute(
                        "INSERT INTO panels (id, dashboard_id, name, created_at, updated_at) "
                        "VALUES ('extra', 'd', 'Extra', 't', 't')"
                    )
        assert PanelRepository(competing).update("z", {"name": "Independent"}).name == "Independent"
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        write(
            SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy)),
            expected=SqlScriptRepository(db).read("d").revision,
        )
        assert PanelRepository(db).get("z").name == "Independent"
    finally:
        writer.close()
        competing.close()


def test_change_committed_after_validation_still_conflicts_with_batch(db):
    writer, competing = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)
    changed = False

    def execute(sql, *args):
        nonlocal changed
        if sql.startswith("UPDATE dashboards") and not changed:
            changed = True
            PanelRepository(competing).update("b", {"name": "Changed after validation"})
        return writer.execute(sql, *args)

    proxy.execute.side_effect = execute
    try:
        with pytest.raises(SqlScriptWriteConflict):
            write(SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy)))
        assert PanelRepository(db).get("b").name == "Changed after validation"
        assert PanelRepository(db).get("a").sql_content == "SELECT 1"
        assert rows(db)["dashboard_sql_scripts"] == []
        assert DashboardRepository(db).get("d").sql_content == ""
    finally:
        writer.close()
        competing.close()


def test_dashboard_deletion_removes_only_its_publication(db):
    repo = SqlScriptRepository(db)
    write(repo)
    write(
        repo,
        dashboard="other",
        source="SELECT 9",
        sqls=("SELECT 9",),
        choices=[KeepSqlPanel(0, "z")],
    )
    DashboardRepository(db).delete("d")
    assert db.execute("SELECT dashboard_id FROM dashboard_sql_scripts").fetchall() == [("other",)]


def test_constraint_failure_after_creating_rows_rolls_back_the_batch(db):
    db.execute("CREATE TABLE retained (panel_id VARCHAR REFERENCES panels(id))")
    db.execute("INSERT INTO retained VALUES ('a')")
    before = rows(db)
    with pytest.raises(SqlScriptWriteConflict):
        write(SqlScriptRepository(db))
    assert rows(db) == before


def test_two_publishers_conflict_on_one_dashboard_but_other_dashboard_can_commit(db):
    writer, competing = db.cursor(), db.cursor()
    expected = SqlScriptRepository(db).read("d").revision
    proxy = Mock(wraps=writer)

    def commit():
        repo = SqlScriptRepository(competing)
        with pytest.raises(SqlScriptWriteConflict):
            write(repo, expected=expected)
        write(
            repo,
            dashboard="other",
            source="SELECT 9",
            sqls=("SELECT 9",),
            choices=[KeepSqlPanel(0, "z")],
        )
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        result = write(
            SqlScriptRepository(cast(duckdb.DuckDBPyConnection, proxy)), expected=expected
        )
        assert SqlScriptRepository(db).read("d") == result.snapshot
        assert SqlScriptRepository(db).read("other").publication.revision == 1
    finally:
        writer.close()
        competing.close()


@pytest.mark.parametrize("revision", [None, True, "", "sql-script-v1:" + "z" * 64])
def test_invalid_revision_is_rejected_before_parsing_or_writes(db, revision):
    parse = Mock()
    before = rows(db)
    with pytest.raises(ValueError):
        SqlScriptRepository(db).write("d", revision, "SELECT 1", [], parse=parse)
    parse.assert_not_called()
    assert rows(db) == before


def test_revision_exhaustion_does_not_wrap_or_write(db):
    repo = SqlScriptRepository(db)
    write(repo)
    db.execute("UPDATE dashboard_sql_scripts SET revision = ?", [2**63 - 1])
    before = rows(db)
    with pytest.raises(ValueError, match="exhausted"):
        write(repo)
    assert rows(db) == before


def test_failure_deleting_script_metadata_rolls_back_dashboard_and_panels(db):
    write(SqlScriptRepository(db))
    db.execute("ALTER TABLE dashboard_sql_scripts RENAME TO saved_sql_scripts")
    db.execute("CREATE VIEW dashboard_sql_scripts AS SELECT * FROM saved_sql_scripts")
    before = rows(db)
    with pytest.raises(duckdb.Error):
        DashboardRepository(db).delete("d")
    assert rows(db) == before
