"""Native parser + internal atomic writer, with no new HTTP mutation endpoint."""

from __future__ import annotations

import pytest
from sqlviz_api.services.sql_scripts import SqlScriptService
from sqlviz_core.models.sql_reconciliation import CreateSqlPanel, KeepSqlPanel, RemoveSqlPanel
from sqlviz_core.models.sql_script import SqlScriptError
from sqlviz_storage.project_db import create_project
from sqlviz_storage.sql_script_repository import SqlScriptRepository


@pytest.fixture
def db():
    conn = create_project(":memory:")
    conn.execute(
        "INSERT INTO dashboards (id, name, created_at, updated_at) VALUES ('d', 'D', 't', 't')"
    )
    yield conn
    conn.close()


def test_full_native_parsing_and_exact_source_roundtrip_do_not_execute_author_sql(db):
    source = "-- 😀 ; comment\nSELECT 'a;b' AS label;\nWITH x AS (SELECT 20) SELECT * FROM x;"
    repo = SqlScriptRepository(db)
    committed = repo.write(
        "d",
        repo.read("d").revision,
        source,
        [CreateSqlPanel(0, "first"), CreateSqlPanel(1, "second")],
        parse=SqlScriptService().parse,
    )
    publication = committed.snapshot.publication
    assert publication.source == source
    assert [
        item.sql_content
        for item in sorted(committed.snapshot.panels, key=lambda panel: panel.sort_order)
    ] == [
        "-- 😀 ; comment\nSELECT 'a;b' AS label",
        "WITH x AS (SELECT 20) SELECT * FROM x;",
    ]
    assert dict(committed.created_panels)["first"] == publication.bindings[0].panel_id
    assert dict(committed.created_panels)["second"] == publication.bindings[1].panel_id
    assert repo.read("d") == committed.snapshot


def test_invalid_later_statement_aborts_before_any_metadata_write(db):
    repo = SqlScriptRepository(db)
    before = repo.read("d")
    with pytest.raises(SqlScriptError):
        repo.write(
            "d",
            before.revision,
            "SELECT 1; SELECT 'unfinished",
            [CreateSqlPanel(0, "a"), CreateSqlPanel(1, "b")],
            parse=SqlScriptService().parse,
        )
    assert repo.read("d") == before
    assert db.execute("SELECT count(*) FROM panels").fetchone() == (0,)


def test_parsing_never_executes_statements_in_project_catalog(db):
    repo = SqlScriptRepository(db)
    repo.write(
        "d",
        repo.read("d").revision,
        "CREATE TABLE never_executed (x INTEGER)",
        [CreateSqlPanel(0, "definition")],
        parse=SqlScriptService().parse,
    )
    assert db.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = 'never_executed'"
    ).fetchone() == (0,)
    # Statement eligibility is a separate application policy, not a storage side effect.


def test_comment_only_script_removes_panels_only_with_explicit_decisions(db):
    repo = SqlScriptRepository(db)
    parse = SqlScriptService().parse
    first = repo.write(
        "d", repo.read("d").revision, "SELECT 1", [CreateSqlPanel(0, "one")], parse=parse
    )
    panel_id = first.created_panels[0][1]
    empty = repo.write(
        "d", first.snapshot.revision, "-- no queries;", [RemoveSqlPanel(panel_id)], parse=parse
    )
    assert empty.snapshot.panels == () and empty.snapshot.publication.bindings == ()


def test_parsed_unicode_reordering_preserves_explicit_ids(db):
    repo = SqlScriptRepository(db)
    parse = SqlScriptService().parse
    first = repo.write(
        "d",
        repo.read("d").revision,
        "SELECT '😀'; SELECT 2",
        [CreateSqlPanel(0, "one"), CreateSqlPanel(1, "two")],
        parse=parse,
    )
    ids = dict(first.created_panels)
    second = repo.write(
        "d",
        first.snapshot.revision,
        "SELECT 2; SELECT '😀'",
        [KeepSqlPanel(0, ids["two"]), KeepSqlPanel(1, ids["one"])],
        parse=parse,
    )
    assert [binding.panel_id for binding in second.snapshot.publication.bindings] == [
        ids["two"],
        ids["one"],
    ]
