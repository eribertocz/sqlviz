"""Invalid values have no side effects; optional learning is independently atomic."""

from collections.abc import Iterator

import duckdb
import pytest
import sqlviz_storage.override_system as overrides
from sqlviz_storage import brain_db
from sqlviz_storage.brain_db import get_layout_pattern
from sqlviz_storage.panel_repository import PanelWriteConflict
from sqlviz_storage.project_db import create_project


@pytest.fixture(autouse=True)
def isolated_brain(monkeypatch):
    brain = duckdb.connect(":memory:")
    brain_db._ensure_tables(brain)
    monkeypatch.setattr(brain_db, "_brain_conn", brain)
    yield
    brain.close()


@pytest.fixture
def db(tmp_path) -> Iterator[duckdb.DuckDBPyConnection]:
    conn = create_project(str(tmp_path / "sizes.sqlviz"))
    conn.execute("INSERT INTO dashboards (id, name, created_at, updated_at) "
                 "VALUES ('d', 'D', 'before', 'before')")
    conn.execute("INSERT INTO panels (id, dashboard_id, name, sql_content, "
                 "sort_order, created_at, updated_at) "
                 "VALUES ('p', 'd', 'P', 'SELECT 1', 0, 'before', 'before')")
    overrides.store_inference(conn, "p", "fingerprint", "bar", 12, 360)
    yield conn
    conn.close()


@pytest.mark.parametrize("field,value", [
    ("col_span", "-7"), ("col_span", "0"), ("col_span", "13"),
    ("col_span", "1.5"), ("col_span", " 6"), ("col_span", "６"),
    ("height_px", "119"), ("height_px", "901"), ("height_px", "1e3"),
    ("height_px", "9" * 5000), ("unknown", "6"),
])
def test_invalid_write_never_opens_brain_or_changes_project(db, field, value):
    before = db.execute("SELECT * FROM panels").fetchall()

    def unavailable():
        pytest.fail("Validation must precede optional learning")

    with pytest.raises(ValueError):
        overrides.apply_override(db, unavailable, "p", field, value)
    assert db.execute("SELECT * FROM panels").fetchall() == before


def test_unavailable_learning_does_not_report_a_failed_save(db, caplog):
    def unavailable():
        raise OSError("secret database path")

    overrides.apply_override(db, unavailable, "p", "col_span", "6")
    assert db.execute("SELECT selected_col_span, col_span_user_override, "
                      "inferred_col_span FROM panels").fetchone() == (6, 6, 12)
    assert "optional learning was not recorded" in caplog.text
    assert "secret database path" not in caplog.text


def test_project_failure_never_teaches_brain(db):
    with db.cursor() as writer:
        writer.execute("BEGIN")
        writer.execute("UPDATE panels SET selected_col_span = 8 WHERE id = 'p'")
        with pytest.raises(PanelWriteConflict):
            overrides.apply_override(db, lambda: pytest.fail("No learning after failed save"),
                                     "p", "col_span", "6")
        writer.execute("ROLLBACK")
    assert db.execute("SELECT selected_col_span, col_span_user_override "
                      "FROM panels").fetchone() == (12, None)


def test_learning_event_failure_rolls_back_pattern_and_preserves_save(db, monkeypatch):
    from sqlviz_storage.brain_db import get_brain_connection

    brain = get_brain_connection()

    def fail(*args, **kwargs):
        raise RuntimeError("simulated event failure")

    monkeypatch.setattr(overrides, "_log_event", fail)
    overrides.apply_override(db, brain, "p", "height_px", "480")
    assert get_layout_pattern(brain, "fingerprint") is None
    assert db.execute("SELECT height_user_override FROM panels").fetchone() == (480,)


@pytest.mark.parametrize("fields", [
    [("col_span", "6"), ("height_px", "480")],
    [("height_px", "480"), ("col_span", "6")],
])
def test_learning_keeps_both_dimensions(db, fields):
    from sqlviz_storage.brain_db import get_brain_connection

    brain = get_brain_connection()
    for field, value in fields:
        overrides.apply_override(db, brain, "p", field, value)
    assert get_layout_pattern(brain, "fingerprint") == {"col_span": 6, "height_px": 480}
    assert brain.execute("SELECT count(*) FROM feedback_events").fetchone() == (2,)


def test_invalid_historical_overrides_are_ignored_without_mutating_result_dimensions():
    ir = {"col_span": 12, "panel_height_px": 360}
    assert overrides.apply_layout_overrides(ir, -7, 0) == ir
    assert ir == {"col_span": 12, "panel_height_px": 360}


def test_clear_follows_latest_inference_not_the_original_value(db):
    from sqlviz_storage.brain_db import get_brain_connection

    overrides.apply_override(db, get_brain_connection(), "p", "col_span", "6")
    overrides.store_inference(db, "p", "fingerprint", "bar", 8, 400)
    overrides.clear_override(db, "p", "col_span")
    assert db.execute("SELECT inferred_col_span, selected_col_span, "
                      "col_span_user_override FROM panels").fetchone() == (8, 8, None)


def test_saved_dimensions_and_reset_survive_reopening(db, tmp_path):
    brain = brain_db.get_brain_connection()
    overrides.apply_override(db, brain, "p", "col_span", "1")
    overrides.apply_override(db, brain, "p", "height_px", "900")
    db.close()
    with duckdb.connect(str(tmp_path / "sizes.sqlviz")) as reopened:
        assert reopened.execute("SELECT selected_col_span, selected_height_px "
                                "FROM panels").fetchone() == (1, 900)
        overrides.clear_override(reopened, "p", "height_px")
    with duckdb.connect(str(tmp_path / "sizes.sqlviz")) as reopened:
        assert reopened.execute("SELECT selected_col_span, selected_height_px, "
                                "height_user_override FROM panels").fetchone() == (1, 360, None)
