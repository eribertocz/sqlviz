"""A confirmed project choice precedes learning and survives deletion races."""

from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_storage import brain_db
from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.override_system import apply_override, clear_override, store_inference
from sqlviz_storage.panel_repository import PanelNotFound, PanelRepository, PanelWriteConflict
from sqlviz_storage.project_db import create_project, open_project


def seed(db):
    db.execute("INSERT INTO dashboards (id, name, created_at, updated_at) "
               "VALUES ('d', 'D', 'before', 'before')")
    db.execute("INSERT INTO panels (id, dashboard_id, name, sql_content, created_at, "
               "updated_at, fingerprint, inferred_chart_type, selected_chart_type, "
               "view_title, col_span_user_override) VALUES "
               "('p', 'd', 'P', 'SELECT 1', 'before', 'before', 'fp', 'bar', 'bar', 'Keep', 6)")


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


@pytest.mark.parametrize("value", ["line", "bar", None])
def test_only_selected_override_and_timestamp_change(db, value):
    before = PanelRepository(db).get("p")
    saved = PanelRepository(db).set_override("p", "chart_type", value)
    assert saved.__dict__ == {
        **before.__dict__, "selected_chart_type": value or "bar",
        "chart_user_override": value, "updated_at": saved.updated_at,
    }
    assert saved.updated_at != before.updated_at
    assert PanelRepository(db).get("p") == saved


@pytest.mark.parametrize("stage", ["read", "commit"])
@pytest.mark.parametrize("value", ["line", None])
def test_failure_after_write_rolls_back_and_never_starts_learning(db, stage, value):
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
        proxy.commit.side_effect = duckdb.TransactionException("synthetic commit failure")
    learning = Mock(side_effect=AssertionError("Must not learn an uncommitted choice"))
    connection = cast(duckdb.DuckDBPyConnection, proxy)
    with pytest.raises(PanelWriteConflict if stage == "commit" else RuntimeError):
        if value is None:
            clear_override(connection, "p", "chart_type")
        else:
            apply_override(connection, learning, "p", "chart_type", value)
    assert snapshot(db) == before
    learning.assert_not_called()


@pytest.mark.parametrize("target", ["panel", "dashboard"])
@pytest.mark.parametrize("value", ["line", None])
def test_concurrent_deletion_never_confirms_or_teaches_a_choice(db, target, value):
    with db.cursor() as writer, db.cursor() as deleting:
        proxy = Mock(wraps=writer)

        def execute(sql, parameters):
            if sql.startswith("UPDATE panels"):
                if target == "panel":
                    PanelRepository(deleting).delete("p")
                else:
                    DashboardRepository(deleting).delete("d")
            return writer.execute(sql, parameters)

        proxy.execute.side_effect = execute
        learning = Mock(side_effect=AssertionError("No learning after deletion"))
        with pytest.raises(PanelWriteConflict):
            if value is None:
                clear_override(cast(duckdb.DuckDBPyConnection, proxy), "p", "chart_type")
            else:
                apply_override(cast(duckdb.DuckDBPyConnection, proxy), learning,
                               "p", "chart_type", value)
        learning.assert_not_called()
    with pytest.raises(PanelNotFound):
        PanelRepository(db).get("p")


def test_learning_failure_keeps_confirmed_snapshot_and_redacts_exception(db, caplog):
    learning = Mock(side_effect=OSError("secret path and SQL"))
    saved = apply_override(db, learning, "p", "chart_type", "line")
    assert saved == PanelRepository(db).get("p")
    assert saved.chart_user_override == "line"
    assert "optional learning was not recorded" in caplog.text
    assert "secret path" not in caplog.text


def test_learning_observes_a_committed_project_and_cannot_change_api_snapshot(db):
    def learn():
        with db.cursor() as reader:
            assert PanelRepository(reader).get("p").chart_user_override == "line"
            PanelRepository(reader).set_override("p", "chart_type", "pie")
        raise OSError("optional learning unavailable")
    saved = apply_override(db, learn, "p", "chart_type", "line")
    assert saved.chart_user_override == "line"
    assert PanelRepository(db).get("p").chart_user_override == "pie"


def test_pattern_and_event_roll_back_together_when_learning_fails(db, monkeypatch):
    import sqlviz_storage.override_system as overrides
    brain = duckdb.connect(":memory:")
    brain_db._ensure_tables(brain)
    monkeypatch.setattr(overrides, "_log_event", Mock(side_effect=RuntimeError("event failure")))
    try:
        saved = apply_override(db, brain, "p", "chart_type", "line")
        assert saved.chart_user_override == "line"
        assert brain_db.get_chart_pattern(brain, "fp") is None
        assert brain.execute("SELECT count(*) FROM feedback_events").fetchone() == (0,)
    finally:
        brain.close()


def test_reset_follows_latest_inference_and_reopening_keeps_it(tmp_path):
    path = str(tmp_path / "synthetic.sqlviz")
    conn = create_project(path)
    try:
        seed(conn)
        PanelRepository(conn).set_override("p", "chart_type", "bar")
        store_inference(conn, "p", "fp", "line", 12, 360)
        saved = clear_override(conn, "p", "chart_type")
        assert saved.chart_user_override is None and saved.selected_chart_type == "line"
    finally:
        conn.close()
    reopened = open_project(path)
    try:
        assert PanelRepository(reopened).get("p") == saved
        store_inference(reopened, "p", "fp", "pie", 12, 360)
        assert PanelRepository(reopened).get("p").selected_chart_type == "pie"
    finally:
        reopened.close()
