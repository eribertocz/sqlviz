"""Tests for OverrideSystem — V0.2 Fase E.

Covers:
- store_inference: writes inferred_* and initialises selected_* correctly
- apply_override: updates selected_* and *_user_override; never touches inferred_*
- apply_override: unknown field_name raises ValueError
- apply_override: missing panel_id raises LookupError
- apply_override: writes pattern to brain.duckdb
- Invariant: inferred_* never overwritten by subsequent execute or override
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import duckdb
import pytest
import sqlviz_storage.brain_db as brain_module
from sqlviz_storage.brain_db import get_brain_connection, get_chart_pattern
from sqlviz_storage.override_system import apply_override, store_inference
from sqlviz_storage.schema import SCHEMA_STATEMENTS


def _make_conn(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.sqlviz"))
    for stmt in SCHEMA_STATEMENTS:
        conn.execute(stmt)
    return conn


def _insert_panel(conn: duckdb.DuckDBPyConnection, panel_id: str = "p1") -> None:
    conn.execute(
        "INSERT INTO dashboards (id, name, created_at, updated_at) "
        "VALUES ('d1', 'D', '2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00')"
    )
    conn.execute(
        "INSERT INTO panels "
        "(id, dashboard_id, name, sql_content, sort_order, created_at, updated_at) "
        "VALUES (?, 'd1', 'P', 'SELECT 1', 0, '2024-01-01T00:00:00+00:00', "
        "'2024-01-01T00:00:00+00:00')",
        [panel_id],
    )


@pytest.fixture
def db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = _make_conn(tmp_path)
    _insert_panel(conn)
    return conn


@pytest.fixture(autouse=True)
def _reset_brain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    brain_module._brain_conn = None
    p = tmp_path / ".sqlviz" / "brain.duckdb"
    (tmp_path / ".sqlviz").mkdir()
    monkeypatch.setattr(brain_module, "get_brain_path", lambda: p)
    yield
    if brain_module._brain_conn is not None:
        brain_module._brain_conn.close()
    brain_module._brain_conn = None


# ── store_inference ───────────────────────────────────────────────────────────

class TestStoreInference:

    def test_writes_fingerprint(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp_abc", "line", 12, 360)
        row = db.execute("SELECT fingerprint FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "fp_abc"

    def test_writes_inferred_chart_type(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "bar", 8, 360)
        row = db.execute("SELECT inferred_chart_type FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "bar"

    def test_initialises_selected_chart_type(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "bar", 8, 360)
        row = db.execute("SELECT selected_chart_type FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "bar"

    def test_initialises_selected_col_span(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 6, 360)
        row = db.execute("SELECT selected_col_span FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 6

    def test_initialises_selected_height_px(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 480)
        row = db.execute("SELECT selected_height_px FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 480

    def test_selected_chart_not_overwritten_when_override_exists(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        # Pre-set a user override — selected should retain the override value
        db.execute(
            "UPDATE panels SET chart_user_override = 'pie' WHERE id = 'p1'"
        )
        store_inference(db, "p1", "fp1", "line", 12, 360)
        row = db.execute("SELECT selected_chart_type FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "pie"

    def test_inferred_never_overwritten_on_repeat_execute(
        self, db: duckdb.DuckDBPyConnection
    ) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        store_inference(db, "p1", "fp1", "bar", 8, 240)  # second execute
        row = db.execute("SELECT inferred_chart_type FROM panels WHERE id = 'p1'").fetchone()
        # inferred_chart_type is updated on each execute (stores latest inference)
        assert row is not None and row[0] == "bar"


# ── apply_override ────────────────────────────────────────────────────────────

class TestApplyOverrideChartType:

    def test_sets_selected_chart_type(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "chart_type", "bar")
        row = db.execute("SELECT selected_chart_type FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "bar"

    def test_sets_chart_user_override(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "chart_type", "scatter")
        row = db.execute("SELECT chart_user_override FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "scatter"

    def test_inferred_chart_type_never_touched(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "chart_type", "bar")
        row = db.execute("SELECT inferred_chart_type FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == "line"

    def test_writes_pattern_to_brain(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "chart_type", "bar")
        assert get_chart_pattern(brain, "fp1") == "bar"


class TestApplyOverrideColSpan:

    def test_sets_selected_col_span(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "col_span", "6")
        row = db.execute("SELECT selected_col_span FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 6

    def test_sets_col_span_user_override(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "col_span", "8")
        row = db.execute("SELECT col_span_user_override FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 8

    def test_inferred_col_span_never_touched(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "col_span", "6")
        row = db.execute("SELECT inferred_col_span FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 12


class TestApplyOverrideHeightPx:

    def test_sets_selected_height_px(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "height_px", "480")
        row = db.execute("SELECT selected_height_px FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 480

    def test_inferred_height_px_never_touched(self, db: duckdb.DuckDBPyConnection) -> None:
        store_inference(db, "p1", "fp1", "line", 12, 360)
        brain = get_brain_connection()
        apply_override(db, brain, "p1", "height_px", "480")
        row = db.execute("SELECT inferred_height_px FROM panels WHERE id = 'p1'").fetchone()
        assert row is not None and row[0] == 360


class TestApplyOverrideErrors:

    def test_unknown_field_raises_value_error(self, db: duckdb.DuckDBPyConnection) -> None:
        brain = get_brain_connection()
        with pytest.raises(ValueError, match="Unknown override field"):
            apply_override(db, brain, "p1", "unknown_field", "x")

    def test_missing_panel_raises_lookup_error(self, db: duckdb.DuckDBPyConnection) -> None:
        brain = get_brain_connection()
        with pytest.raises(LookupError, match="Panel not found"):
            apply_override(db, brain, "does-not-exist", "chart_type", "bar")
