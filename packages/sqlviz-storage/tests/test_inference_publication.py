"""Compatible execution inputs, competing cursors and complete metadata rollback."""

from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_storage.dashboard_repository import DashboardRepository, DashboardWriteConflict
from sqlviz_storage.inference_publication import (
    InferencePublicationConflict,
    inference_publication,
)
from sqlviz_storage.override_system import store_inference
from sqlviz_storage.panel_repository import PanelRepository, PanelWriteConflict
from sqlviz_storage.project_db import create_project, open_project


@pytest.fixture
def db():
    conn = create_project(":memory:")
    seed(conn)
    try:
        yield conn
    finally:
        conn.close()


def seed(db):
    for dashboard in ("d", "other"):
        db.execute(
            "INSERT INTO dashboards (id, name, created_at, updated_at, last_run_at, last_run_sql) "
            "VALUES (?, ?, 't', 't', 'previous time', 'previous successful source')",
            [dashboard, dashboard],
        )
    for panel, dashboard in (("p", "d"), ("peer", "d"), ("unrelated", "other")):
        db.execute(
            "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at, "
            "chart_user_override, selected_chart_type, col_span_user_override, selected_col_span, "
            "height_user_override, selected_height_px, view_title) "
            "VALUES (?, ?, ?, 'SELECT 1', 't', 't', 'bar', 'bar', 6, 6, 300, 300, 'My title')",
            [panel, dashboard, panel],
        )


def snapshot(db):
    return {table: db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("dashboards", "panels", "dashboard_sql_scripts")}


def publish(db):
    with inference_publication(db, "p", expected_sql="SELECT 1", expected_chart_override="bar"):
        store_inference(db, "p", "new fingerprint", "line", 12, 400, "trend")
        db.execute("UPDATE dashboards SET dashboard_hint = 'trend' WHERE id = 'd'")


def test_success_preserves_manual_choices_and_last_run_record(db):
    before_panel = PanelRepository(db).get("p")
    before_parent = DashboardRepository(db).get("d")
    publish(db)
    panel = PanelRepository(db).get("p")
    parent = DashboardRepository(db).get("d")
    assert panel.fingerprint == "new fingerprint"
    assert panel.inferred_chart_type == "line"
    assert panel.selected_chart_type == panel.chart_user_override == "bar"
    assert panel.selected_col_span == panel.col_span_user_override == 6
    assert panel.selected_height_px == panel.height_user_override == 300
    assert panel.view_title == "My title"
    assert parent.dashboard_hint == "trend"
    assert parent.last_run_at == before_parent.last_run_at
    assert parent.last_run_sql == before_parent.last_run_sql
    assert panel.updated_at != before_panel.updated_at
    assert parent.updated_at != before_parent.updated_at


@pytest.mark.parametrize("sql", ["SELECT 2", "SELECT 1 ", "select 1", "-- ñ;\nSELECT 1"])
def test_exact_input_compatibility_never_uses_sql_normalization(db, sql):
    PanelRepository(db).update("p", {"sql_content": sql})
    before = snapshot(db)
    with pytest.raises(InferencePublicationConflict):
        publish(db)
    assert snapshot(db) == before


@pytest.mark.parametrize("override", [None, "pie"])
def test_changed_or_cleared_chart_choice_invalidates_the_captured_inference(db, override):
    PanelRepository(db).set_override("p", "chart_type", override)
    before = snapshot(db)
    with pytest.raises(InferencePublicationConflict):
        publish(db)
    assert snapshot(db) == before


@pytest.mark.parametrize("missing", ["panel", "parent"])
def test_removed_inputs_fail_without_touching_another_panel(db, missing):
    if missing == "panel":
        PanelRepository(db).delete("p")
    else:
        db.execute("DELETE FROM dashboards WHERE id = 'd'")  # Legacy orphan.
    before = snapshot(db)
    with pytest.raises(InferencePublicationConflict):
        publish(db)
    assert snapshot(db) == before


def test_callback_failure_rolls_back_inference_classification_and_timestamps(db):
    before = snapshot(db)
    with pytest.raises(ValueError, match="classification write failed"):
        with inference_publication(
            db, "p", expected_sql="SELECT 1", expected_chart_override="bar",
        ):
            store_inference(db, "p", "new", "line", 12, 400, "trend")
            db.execute("UPDATE dashboards SET dashboard_hint = 'trend' WHERE id = 'd'")
            raise ValueError("classification write failed")
    assert snapshot(db) == before
    publish(db)  # The connection is usable after rollback.


@pytest.mark.parametrize("column, value", [
    ("sql_content", "SELECT 2"), ("chart_user_override", "pie"),
])
def test_conditional_fence_rejects_an_incompatible_body_and_rolls_everything_back(
    db, column, value,
):
    before = snapshot(db)
    with pytest.raises(InferencePublicationConflict):
        with inference_publication(
            db, "p", expected_sql="SELECT 1", expected_chart_override="bar",
        ):
            store_inference(db, "p", "new", "line", 12, 400, "trend")
            db.execute(f"UPDATE panels SET {column} = ? WHERE id = 'p'", [value])
    assert snapshot(db) == before


def test_committed_sql_edit_after_the_guard_read_is_detected_by_duckdb(db, monkeypatch):
    writer, competing = db.cursor(), db.cursor()
    original = PanelRepository.get
    changed = False

    def racing_get(repository, panel_id):
        nonlocal changed
        panel = original(repository, panel_id)
        if repository._db is writer and not changed:
            changed = True
            PanelRepository(competing).update("p", {"sql_content": "SELECT 2"})
        return panel

    monkeypatch.setattr(PanelRepository, "get", racing_get)
    try:
        with pytest.raises(InferencePublicationConflict):
            publish(writer)
        assert PanelRepository(db).get("p").sql_content == "SELECT 2"
        assert PanelRepository(db).get("p").fingerprint is None
        assert DashboardRepository(db).get("d").dashboard_hint is None
        assert DashboardRepository(db).get("d").updated_at == "t"
    finally:
        writer.close()
        competing.close()


def test_publication_fences_competing_panel_and_parent_writes_but_not_other_dashboards(db):
    writer, competing = db.cursor(), db.cursor()
    try:
        with inference_publication(
            writer, "p", expected_sql="SELECT 1", expected_chart_override="bar",
        ):
            store_inference(writer, "p", "new", "line", 12, 400, "trend")
            with pytest.raises(PanelWriteConflict):
                PanelRepository(competing).update("p", {"sql_content": "SELECT 2"})
            with pytest.raises(PanelWriteConflict):
                PanelRepository(competing).delete("p")
            with pytest.raises(DashboardWriteConflict):
                DashboardRepository(competing).delete("d")
            assert PanelRepository(competing).update("unrelated", {"name": "Independent"}).name == (
                "Independent"
            )
        assert PanelRepository(db).get("p").fingerprint == "new"
        assert PanelRepository(db).get("p").sql_content == "SELECT 1"
    finally:
        writer.close()
        competing.close()


@pytest.mark.parametrize("fail", [False, True])
def test_commit_failure_and_reopening_keep_only_confirmed_metadata(tmp_path, fail):
    path = str(tmp_path / "synthetic.sqlviz")
    db = create_project(path)
    try:
        seed(db)
        before = snapshot(db)
        if fail:
            proxy = Mock(wraps=db)
            proxy.commit.side_effect = duckdb.TransactionException("private synthetic conflict")
            with pytest.raises(InferencePublicationConflict):
                publish(cast(duckdb.DuckDBPyConnection, proxy))
        else:
            publish(db)
        after = snapshot(db)
        assert (after == before) is fail
    finally:
        db.close()
    reopened = open_project(path)
    try:
        assert snapshot(reopened) == after
        publish(reopened)
    finally:
        reopened.close()
