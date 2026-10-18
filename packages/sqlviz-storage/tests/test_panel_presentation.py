"""Presentation persistence uses the panel's transaction and deletion fence."""

from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.panel_repository import PanelNotFound, PanelRepository, PanelWriteConflict
from sqlviz_storage.panel_view_overrides import set_view_override
from sqlviz_storage.project_db import create_project, open_project


def seed(db):
    db.execute("INSERT INTO dashboards (id, name, created_at, updated_at) "
               "VALUES ('d', 'D', 'created', 'before')")
    for key in ("p", "other"):
        db.execute("INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, "
                   "updated_at, view_title, view_x_label, view_y_label, fingerprint, "
                   "selected_col_span, col_span_user_override) VALUES "
                   "(?, 'd', ?, 'SELECT 1', 'created', 'before', 'Title', 'Year', 'Revenue', "
                   "'fp', 6, 6)", [key, key])


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
            for table in ("panels", "dashboards", "_sqlviz_meta")}


@pytest.mark.parametrize("field,column", [
    ("title", "view_title"), ("x_label", "view_x_label"), ("y_label", "view_y_label"),
])
@pytest.mark.parametrize("value", [None, "", "  Nueva etiqueta · ñ  "])
def test_only_the_requested_field_and_timestamp_change(db, field, column, value):
    before = PanelRepository(db).get("p")
    other = PanelRepository(db).get("other")
    parent = DashboardRepository(db).get("d")
    result = PanelRepository(db).set_presentation("p", field, value)
    expected = {**before.__dict__, column: value or None, "updated_at": result.updated_at}
    assert result.__dict__ == expected
    assert result.updated_at != before.updated_at
    assert PanelRepository(db).get("p") == result
    assert PanelRepository(db).get("other") == other
    assert DashboardRepository(db).get("d") == parent


def test_invalid_and_missing_writes_do_not_mutate_rows(db):
    before = snapshot(db)
    with pytest.raises(ValueError):
        PanelRepository(db).set_presentation("p", "name", "After")
    with pytest.raises(ValueError):
        set_view_override(db, "p", "title", " ")
    with pytest.raises(PanelNotFound):
        set_view_override(db, "missing", "title", "After")
    assert snapshot(db) == before


@pytest.mark.parametrize("stage", ["read", "commit"])
def test_failure_after_writing_rolls_back_value_and_timestamp(db, stage):
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
        return result

    proxy.execute.side_effect = execute
    if stage == "commit":
        proxy.commit.side_effect = duckdb.TransactionException("synthetic conflict")
    with pytest.raises(PanelWriteConflict if stage == "commit" else RuntimeError):
        PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).set_presentation(
            "p", "title", "After",
        )
    assert snapshot(db) == before


@pytest.mark.parametrize("fail", [False, True])
def test_reopened_project_keeps_only_confirmed_presentation(tmp_path, fail):
    path = str(tmp_path / "synthetic.sqlviz")
    conn = create_project(path)
    try:
        seed(conn)
        before = snapshot(conn)
        if fail:
            proxy = Mock(wraps=conn)
            proxy.commit.side_effect = duckdb.TransactionException("synthetic conflict")
            with pytest.raises(PanelWriteConflict):
                PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).set_presentation(
                    "p", "x_label", None,
                )
        else:
            PanelRepository(conn).set_presentation("p", "x_label", None)
            set_view_override(conn, "p", "title", "  Guardado · ñ  ")
        after = snapshot(conn)
    finally:
        conn.close()
    reopened = open_project(path)
    try:
        assert snapshot(reopened) == after
        if fail:
            assert after == before
        else:
            panel = PanelRepository(reopened).get("p")
            assert panel.view_x_label is None and panel.view_title == "  Guardado · ñ  "
    finally:
        reopened.close()


@pytest.mark.parametrize("target", ["panel", "dashboard"])
def test_deletion_between_read_and_write_never_reports_a_saved_label(db, target):
    writer, deleting = db.cursor(), db.cursor()
    proxy = Mock(wraps=writer)

    def execute(sql, parameters):
        if sql.startswith("UPDATE panels"):
            if target == "panel":
                PanelRepository(deleting).delete("p")
            else:
                DashboardRepository(deleting).delete("d")
        return writer.execute(sql, parameters)

    proxy.execute.side_effect = execute
    try:
        with pytest.raises(PanelWriteConflict):
            PanelRepository(cast(duckdb.DuckDBPyConnection, proxy)).set_presentation(
                "p", "title", "After",
            )
        with pytest.raises(PanelNotFound):
            PanelRepository(db).get("p")
    finally:
        writer.close()
        deleting.close()
