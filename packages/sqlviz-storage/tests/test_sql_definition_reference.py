"""Definition references exclude derived metadata but fence every SQL dependency."""

import pytest
from sqlviz_core.models.sql_reconciliation import KeepSqlPanel
from sqlviz_core.models.sql_script import SqlStatement
from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.inference_publication import InferencePublicationConflict, inference_publication
from sqlviz_storage.override_system import store_inference
from sqlviz_storage.panel_repository import PanelRepository, PanelWriteConflict
from sqlviz_storage.project_db import create_project
from sqlviz_storage.sql_script_repository import (
    SqlDefinitionConflict,
    SqlDefinitionReference,
    SqlScriptRepository,
    SqlScriptWriteConflict,
    definition_revision,
)
from sqlviz_storage.transactions import project_transaction

SOURCE = "SELECT 1; SELECT 2"
STATEMENTS = (SqlStatement("SELECT 1", 0, 8), SqlStatement("SELECT 2", 10, 18))
CHOICES = (KeepSqlPanel(0, "a"), KeepSqlPanel(1, "b"))


@pytest.fixture
def db():
    conn = create_project(":memory:")
    for owner in ("d", "other"):
        conn.execute(
            "INSERT INTO dashboards (id, name, created_at, updated_at) VALUES (?, ?, 't', 't')",
            [owner, owner],
        )
    for panel, owner, sql in (
        ("a", "d", "SELECT 1"),
        ("b", "d", "SELECT 2"),
        ("z", "other", "SELECT 3"),
    ):
        conn.execute(
            "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 't', 't')",
            [panel, owner, panel, sql],
        )
    repository = SqlScriptRepository(conn)
    repository.write(
        "d", repository.read("d").revision, SOURCE, CHOICES, parse=lambda _: STATEMENTS
    )
    try:
        yield conn
    finally:
        conn.close()


def reference(db):
    revision = definition_revision(SqlScriptRepository(db).read("d"))
    assert revision is not None
    return SqlDefinitionReference("d", revision)


def state(db):
    return {
        table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        for table in ("dashboards", "panels", "dashboard_sql_scripts")
    }


def test_derived_metadata_and_drafts_do_not_invalidate_the_definition(db):
    expected = reference(db)
    before = SqlScriptRepository(db).read("d")
    DashboardRepository(db).update("d", {"sql_content": "SELECT 'new draft'"})
    PanelRepository(db).set_presentation("b", "title", "My peer title")
    with inference_publication(
        db, "a", expected_sql="SELECT 1", expected_chart_override=None, definition=expected
    ):
        store_inference(db, "a", "fingerprint", "kpi", 6, 240, "kpi")
    after = SqlScriptRepository(db).read("d")
    assert after.revision != before.revision
    assert definition_revision(after) == expected.revision
    assert PanelRepository(db).get("b").view_title == "My peer title"


def test_identical_recommit_has_a_distinct_definition_reference(db):
    expected = reference(db)
    repository = SqlScriptRepository(db)
    repository.write(
        "d", repository.read("d").revision, SOURCE, CHOICES, parse=lambda _: STATEMENTS
    )
    assert reference(db) != expected
    with project_transaction(db), pytest.raises(SqlDefinitionConflict):
        repository.require_definition(expected)


def test_guard_rejects_a_peer_edit_committed_after_the_definition_snapshot_was_read(
    db, monkeypatch
):
    expected = reference(db)
    writer, competing = db.cursor(), db.cursor()
    original = SqlScriptRepository.require_definition

    def racing(repository, wanted):
        result = original(repository, wanted)
        PanelRepository(competing).update("b", {"sql_content": "SELECT 99"})
        return result

    monkeypatch.setattr(SqlScriptRepository, "require_definition", racing)
    try:
        with pytest.raises(InferencePublicationConflict):
            with inference_publication(
                writer,
                "a",
                expected_sql="SELECT 1",
                expected_chart_override=None,
                definition=expected,
            ):
                store_inference(writer, "a", "obsolete", "kpi", 6, 240, "kpi")
        assert PanelRepository(db).get("b").sql_content == "SELECT 99"
        assert PanelRepository(db).get("a").fingerprint is None
    finally:
        writer.close()
        competing.close()


def test_bound_publication_conflicts_with_peer_edits_deletes_and_script_commits(db):
    expected = reference(db)
    writer, competing = db.cursor(), db.cursor()
    try:
        with inference_publication(
            writer, "a", expected_sql="SELECT 1", expected_chart_override=None, definition=expected
        ):
            store_inference(writer, "a", "current", "kpi", 6, 240, "kpi")
            with pytest.raises(PanelWriteConflict):
                PanelRepository(competing).update("b", {"sql_content": "SELECT 99"})
            with pytest.raises(PanelWriteConflict):
                PanelRepository(competing).delete("b")
            repository = SqlScriptRepository(competing)
            with pytest.raises(SqlScriptWriteConflict):
                repository.write(
                    "d", repository.read("d").revision, SOURCE, CHOICES, parse=lambda _: STATEMENTS
                )
            assert PanelRepository(competing).update(
                "z", {"sql_content": "SELECT 4"}
            ).sql_content == ("SELECT 4")
        assert PanelRepository(db).get("a").fingerprint == "current"
        assert PanelRepository(db).get("b").sql_content == "SELECT 2"
        assert reference(db) == expected
    finally:
        writer.close()
        competing.close()


def test_invalid_stale_reference_has_no_metadata_side_effects(db):
    expected = reference(db)
    before = state(db)
    with pytest.raises(SqlDefinitionConflict):
        with inference_publication(
            db,
            "a",
            expected_sql="SELECT 1",
            expected_chart_override=None,
            definition=SqlDefinitionReference("d", expected.revision[:-1] + "X"),
        ):
            raise AssertionError("Invalid definition entered publication body")
    assert state(db) == before
