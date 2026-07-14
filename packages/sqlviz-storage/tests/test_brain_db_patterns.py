"""Tests for brain.duckdb feedback/layout pattern tables — V0.2 Fase E."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_storage.brain_db as brain_module
from sqlviz_inference.contracts.feedback import FeedbackEvent
from sqlviz_storage.brain_db import (
    get_brain_connection,
    get_chart_pattern,
    get_layout_pattern,
    log_feedback_event,
    record_chart_override,
    record_layout_override,
)


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


# ── Table existence ───────────────────────────────────────────────────────────

class TestFeedbackTablesExist:

    def test_feedback_patterns_table_exists(self) -> None:
        conn = get_brain_connection()
        result = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'feedback_patterns'"
        ).fetchone()
        assert result is not None and result[0] == 1

    def test_layout_patterns_table_exists(self) -> None:
        conn = get_brain_connection()
        result = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'layout_patterns'"
        ).fetchone()
        assert result is not None and result[0] == 1

    def test_feedback_events_table_exists(self) -> None:
        conn = get_brain_connection()
        result = conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = 'feedback_events'"
        ).fetchone()
        assert result is not None and result[0] == 1


# ── get_chart_pattern ─────────────────────────────────────────────────────────

class TestGetChartPattern:

    def test_returns_none_for_unknown_fingerprint(self) -> None:
        conn = get_brain_connection()
        assert get_chart_pattern(conn, "fp_unknown") is None

    def test_returns_user_value_after_record(self) -> None:
        conn = get_brain_connection()
        record_chart_override(conn, "fp1", "line", "bar")
        assert get_chart_pattern(conn, "fp1") == "bar"

    def test_independent_fingerprints(self) -> None:
        conn = get_brain_connection()
        record_chart_override(conn, "fp_a", "pie", "bar")
        record_chart_override(conn, "fp_b", "line", "scatter")
        assert get_chart_pattern(conn, "fp_a") == "bar"
        assert get_chart_pattern(conn, "fp_b") == "scatter"


# ── record_chart_override ────────────────────────────────────────────────────

class TestRecordChartOverride:

    def test_upsert_updates_existing_record(self) -> None:
        conn = get_brain_connection()
        record_chart_override(conn, "fp1", "line", "bar")
        record_chart_override(conn, "fp1", "line", "scatter")
        assert get_chart_pattern(conn, "fp1") == "scatter"

    def test_stores_field_name_as_chart_type(self) -> None:
        conn = get_brain_connection()
        record_chart_override(conn, "fp1", "pie", "bar")
        row = conn.execute(
            "SELECT field_name FROM feedback_patterns WHERE fingerprint = 'fp1'"
        ).fetchone()
        assert row is not None and row[0] == "chart_type"


# ── layout_patterns ───────────────────────────────────────────────────────────

class TestLayoutPatterns:

    def test_returns_none_for_unknown_fingerprint(self) -> None:
        conn = get_brain_connection()
        assert get_layout_pattern(conn, "fp_unknown") is None

    def test_record_and_retrieve_col_span(self) -> None:
        conn = get_brain_connection()
        record_layout_override(conn, "fp1", 6, None)
        result = get_layout_pattern(conn, "fp1")
        assert result is not None
        assert result["col_span"] == 6

    def test_record_and_retrieve_height_px(self) -> None:
        conn = get_brain_connection()
        record_layout_override(conn, "fp1", None, 480)
        result = get_layout_pattern(conn, "fp1")
        assert result is not None
        assert result["height_px"] == 480

    def test_upsert_updates_layout_record(self) -> None:
        conn = get_brain_connection()
        record_layout_override(conn, "fp1", 6, 360)
        record_layout_override(conn, "fp1", 8, 480)
        result = get_layout_pattern(conn, "fp1")
        assert result is not None
        assert result["col_span"] == 8
        assert result["height_px"] == 480


# ── log_feedback_event ────────────────────────────────────────────────────────

class TestLogFeedbackEvent:

    def test_event_is_persisted(self) -> None:
        conn = get_brain_connection()
        event = FeedbackEvent(
            fingerprint="fp1",
            field_name="chart_type",
            inferred_value="line",
            user_value="bar",
            panel_id="panel-1",
            dashboard_id="dash-1",
        )
        log_feedback_event(conn, event)
        count = conn.execute(
            "SELECT COUNT(*) FROM feedback_events WHERE fingerprint = 'fp1'"
        ).fetchone()
        assert count is not None and count[0] == 1

    def test_multiple_events_accumulate(self) -> None:
        conn = get_brain_connection()
        for i in range(3):
            log_feedback_event(
                conn,
                FeedbackEvent(
                    fingerprint=f"fp{i}",
                    field_name="chart_type",
                    inferred_value="line",
                    user_value="bar",
                ),
            )
        count = conn.execute("SELECT COUNT(*) FROM feedback_events").fetchone()
        assert count is not None and count[0] == 3

    def test_event_stores_all_fields(self) -> None:
        conn = get_brain_connection()
        event = FeedbackEvent(
            fingerprint="fpX",
            field_name="chart_type",
            inferred_value="pie",
            user_value="bar",
            panel_id="p1",
            dashboard_id="d1",
        )
        log_feedback_event(conn, event)
        row = conn.execute(
            """
            SELECT fingerprint, field_name, inferred_value, user_value,
                   panel_id, dashboard_id
            FROM feedback_events WHERE fingerprint = 'fpX'
            """
        ).fetchone()
        assert row is not None
        assert row[0] == "fpX"
        assert row[1] == "chart_type"
        assert row[2] == "pie"
        assert row[3] == "bar"
        assert row[4] == "p1"
        assert row[5] == "d1"
