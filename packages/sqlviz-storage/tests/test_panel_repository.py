"""Panel updates preserve visual settings and commit only complete changes."""

from datetime import datetime, timezone
from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
import sqlviz_storage.timestamps as timestamps_module
from sqlviz_storage.dashboard_repository import (
    DashboardNotFound,
    DashboardRepository,
    DashboardWriteConflict,
)
from sqlviz_storage.panel_repository import PanelNotFound, PanelRepository, PanelWriteConflict
from sqlviz_storage.project_db import create_project, open_project


def seed(db):
    for dashboard in ("a", "b"):
        db.execute("INSERT INTO dashboards (id, name, created_at, updated_at) "
                   "VALUES (?, ?, 'created', 'before')", [dashboard, dashboard])
    for key, dashboard in (("a1", "a"), ("a2", "a"), ("b1", "b")):
        db.execute(
            "INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, updated_at, "
            "fingerprint, selected_chart_type, chart_user_override, selected_col_span, "
            "col_span_user_override, selected_height_px, height_user_override, view_title, "
            "view_x_label, view_y_label) VALUES (?, ?, ?, 'SELECT 1', 'created', 'before', "
            "'fp', 'bar', 'bar', 6, 6, 300, 300, 'My title', 'Category', 'Revenue')",
            [key, dashboard, key],
        )


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
            for table in ("dashboards", "panels", "_sqlviz_meta")}


def panel_row(db, key="a1"):
    cursor = db.execute("SELECT * FROM panels WHERE id = ?", [key])
    return dict(zip((column[0] for column in cursor.description), cursor.fetchone(), strict=True))


def test_patch_changes_only_basic_fields_and_preserves_every_visual_column(db):
    before = panel_row(db)
    other = PanelRepository(db).get("a2")
    dashboard = DashboardRepository(db).get("a")
    changes = {"name": "  After  ", "sql_content": "-- ñ\r\nSELECT 'a;b';\n", "sort_order": 0}
    result = PanelRepository(db).update("a1", changes)
    after = panel_row(db)
    assert all(after[key] == value for key, value in changes.items())
    assert after["updated_at"] != before["updated_at"]
    for key in before.keys() - changes.keys() - {"updated_at"}:
        assert after[key] == before[key]
    assert PanelRepository(db).get("a1") == result
    assert PanelRepository(db).get("a2") == other
    assert DashboardRepository(db).get("a") == dashboard


def test_direct_invalid_calls_empty_patch_and_missing_panel_never_write(db):
    before = snapshot(db)
    repository = PanelRepository(db)
    for invalid in ({"name": "After", "sort_order": True}, {"name": None}, {"id": "other"}):
        with pytest.raises(ValueError):
            repository.update("a1", invalid)
    assert repository.update("a1", {}) == repository.get("a1")
    for changes in ({}, {"name": "After"}):
        with pytest.raises(PanelNotFound):
            repository.update("missing", changes)
    assert snapshot(db) == before


def test_legacy_orphan_cannot_be_updated_or_silently_repaired(db):
    db.execute("DELETE FROM dashboards WHERE id = 'a'")
    before = snapshot(db)
    with pytest.raises(DashboardNotFound):
        PanelRepository(db).update("a1", {"name": "After"})
    assert snapshot(db) == before


@pytest.mark.parametrize("stage", ["write", "read", "commit"])
def test_failure_at_each_stage_rolls_back_fields_and_timestamp(db, stage):
    before = snapshot(db)
    proxy = Mock(wraps=db)
    wrote = False

    def execute(sql, parameters):
        nonlocal wrote
        if wrote and sql.startswith("SELECT id, dashboard_id") and stage == "read":
            raise RuntimeError("synthetic read failure")
        result = db.execute(sql, parameters)
        if sql.startswith("UPDATE panels"):
            wrote = True
            if stage == "write":
                raise RuntimeError("synthetic write failure")
        return result

    proxy.execute.side_effect = execute
    if stage == "commit":
        proxy.commit.side_effect = duckdb.TransactionException("synthetic commit conflict")
    with pytest.raises(PanelWriteConflict if stage == "commit" else RuntimeError):
        PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
            "a1", {"name": "After", "sql_content": "", "sort_order": 7},
        )
    assert snapshot(db) == before
    assert PanelRepository(db).update("a1", {"name": "Retry"}).name == "Retry"


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("operation", ["patch", "delete"])
def test_reopening_a_synthetic_file_keeps_only_complete_confirmed_state(tmp_path, fail, operation):
    path = str(tmp_path / "synthetic.sqlviz")
    conn = create_project(path)
    try:
        seed(conn)
        before = snapshot(conn)
        changes = {"name": "After", "sql_content": "-- ñ\r\nSELECT 'a;b';\n", "sort_order": -1}
        if fail:
            proxy = Mock(wraps=conn)
            proxy.commit.side_effect = duckdb.TransactionException("synthetic conflict")
            with pytest.raises(PanelWriteConflict):
                repository = PanelRepository(cast(duckdb.DuckDBPyConnection, proxy))
                if operation == "patch":
                    repository.update("a1", changes)
                else:
                    repository.delete("a1")
        elif operation == "delete":
            PanelRepository(conn).delete("a1")
        else:
            result = PanelRepository(conn).update("a1", changes)
        after = snapshot(conn)
    finally:
        conn.close()
    reopened = open_project(path)
    try:
        assert snapshot(reopened) == after
        if fail:
            assert after == before
        elif operation == "delete":
            with pytest.raises(PanelNotFound):
                PanelRepository(reopened).get("a1")
            assert PanelRepository(reopened).get("a2").name == "a2"
        else:
            assert PanelRepository(reopened).get("a1") == result
            assert result.sql_content == changes["sql_content"]
    finally:
        reopened.close()


def test_same_panel_conflicts_but_another_panel_of_the_same_dashboard_can_commit(db):
    writer, competing = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)

    def commit():
        with pytest.raises(PanelWriteConflict):
            PanelRepository(competing).update("a1", {"name": "Lost"})
        assert PanelRepository(competing).get("a1").name == "a1"
        assert PanelRepository(competing).update("a2", {"name": "Independent"}).name == (
            "Independent"
        )
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        assert PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
            "a1", {"name": "After"},
        ).name == "After"
        assert PanelRepository(competing).get("a2").name == "Independent"
    finally:
        writer.close()
        competing.close()


def test_panel_deletion_fences_an_edit_before_commit(db):
    deleting, editing = db.cursor(), db.cursor()
    proxy = Mock(wraps=deleting)

    def commit():
        with pytest.raises(PanelWriteConflict):
            PanelRepository(editing).update("a1", {"name": "Lost"})
        assert PanelRepository(editing).update("a2", {"name": "Independent"}).name == "Independent"
        deleting.commit()

    proxy.commit.side_effect = commit
    try:
        PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).delete("a1")
        with pytest.raises(PanelNotFound):
            PanelRepository(db).get("a1")
        assert PanelRepository(db).get("a2").name == "Independent"
    finally:
        deleting.close()
        editing.close()


def test_panel_delete_constraint_failure_restores_timestamp_and_row(db):
    db.execute("CREATE TABLE retained (panel_id VARCHAR REFERENCES panels(id))")
    db.execute("INSERT INTO retained VALUES ('a1')")
    before = snapshot(db)
    with pytest.raises(PanelWriteConflict):
        PanelRepository(db).delete("a1")
    assert snapshot(db) == before
    db.execute("DELETE FROM retained")
    PanelRepository(db).delete("a1")


def test_dashboard_bulk_delete_fences_panels_even_when_clock_matches_their_timestamps(
    db, monkeypatch,
):
    fixed = datetime(2026, 10, 7, tzinfo=timezone.utc)

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(timestamps_module, "datetime", FixedClock)
    db.execute("UPDATE panels SET updated_at = ? WHERE dashboard_id = 'a'",
               [fixed.isoformat(timespec="microseconds")])
    deleting, editing = db.cursor(), db.cursor()
    proxy = Mock(wraps=deleting)

    def commit():
        with pytest.raises(PanelWriteConflict):
            PanelRepository(editing).update("a1", {"name": "a1"})
        deleting.commit()

    proxy.commit.side_effect = commit
    try:
        DashboardRepository(cast(duckdb.DuckDBPyConnection, proxy)).delete("a")
        assert PanelRepository(db).list("a") == []
        assert PanelRepository(db).get("b1").name == "b1"
    finally:
        deleting.close()
        editing.close()


def test_reader_keeps_previous_snapshot_until_transaction_ends(db):
    writer, reader = db.cursor(), db.cursor()
    try:
        reader.begin()
        previous = PanelRepository(reader).get("a1")
        result = PanelRepository(writer).update("a1", {"name": "After", "sql_content": ""})
        assert PanelRepository(reader).get("a1") == previous
        reader.commit()
        assert PanelRepository(reader).get("a1") == result
    finally:
        writer.close()
        reader.close()


@pytest.mark.parametrize("target", ["panel", "dashboard"])
def test_deletion_between_read_and_write_cannot_return_a_ghost_panel(db, target):
    writer, deleting = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)

    def execute(sql, parameters):
        if sql.startswith("UPDATE panels"):
            if target == "panel":
                PanelRepository(deleting).delete("a1")
            else:
                DashboardRepository(deleting).delete("a")
        return writer.execute(sql, parameters)

    proxy.execute.side_effect = execute
    try:
        with pytest.raises(PanelWriteConflict):
            PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).update("a1", {"name": "Lost"})
        with pytest.raises(PanelNotFound):
            PanelRepository(db).get("a1")
        assert PanelRepository(db).get("b1").name == "b1"
    finally:
        writer.close()
        deleting.close()


def test_parent_deletion_conflicts_with_a_patch_and_rolls_back_all_owned_rows(db):
    writer, deleting = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)
    before = snapshot(db)

    def commit():
        with pytest.raises(DashboardWriteConflict):
            DashboardRepository(deleting).delete("a")
        assert snapshot(deleting) == before
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        result = PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
            "a1", {"name": "After"},
        )
        assert PanelRepository(db).get("a1") == result
        assert PanelRepository(db).get("a2").name == "a2"
        assert DashboardRepository(db).get("a").updated_at == "before"
        DashboardRepository(deleting).delete("a")
        assert PanelRepository(db).list("a") == []
    finally:
        writer.close()
        deleting.close()


def test_same_field_values_and_equal_clock_still_conflict_with_competing_writes(db, monkeypatch):
    fixed = datetime(2026, 10, 7, tzinfo=timezone.utc)

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(timestamps_module, "datetime", FixedClock)
    db.execute("UPDATE panels SET updated_at = ? WHERE id = 'a1'",
               [fixed.isoformat(timespec="microseconds")])
    writer, competing = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)

    def commit():
        with pytest.raises(PanelWriteConflict):
            PanelRepository(competing).update("a1", {"name": "a1"})
        writer.commit()

    proxy.commit.side_effect = commit
    try:
        result = PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).update(
            "a1", {"name": "a1"},
        )
        assert result.updated_at == "2026-10-07T00:00:00.000001+00:00"
    finally:
        writer.close()
        competing.close()
