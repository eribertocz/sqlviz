"""Tests for FeedbackEngine — V0.2 Fase E (DOC10 §6.14).

Covers:
- run_consult: no-op when brain_conn is None
- run_consult: no-op when fingerprint is UNKNOWN
- run_consult: sets feedback_preferred from brain.duckdb
- run_apply: always a no-op — never changes chart_winner
- run_persist: no-op when brain_conn is None
- run_persist: logs event to feedback_events
- Full round-trip: consult → (no-op apply) → persist
"""

from __future__ import annotations

from pathlib import Path

import duckdb
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.feedback.feedback_engine import FeedbackEngine

engine = FeedbackEngine()


def _brain(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "brain.duckdb"))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback_patterns (
            fingerprint VARCHAR PRIMARY KEY,
            field_name  VARCHAR NOT NULL,
            inferred_value VARCHAR NOT NULL,
            user_value  VARCHAR NOT NULL,
            updated_at  VARCHAR NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback_events (
            id             VARCHAR PRIMARY KEY,
            fingerprint    VARCHAR NOT NULL,
            field_name     VARCHAR NOT NULL,
            inferred_value VARCHAR NOT NULL,
            user_value     VARCHAR NOT NULL,
            panel_id       VARCHAR,
            dashboard_id   VARCHAR,
            created_at     VARCHAR NOT NULL
        )
        """
    )
    return conn


def _ctx(fingerprint: str = "fp1", chart_winner: str = "line",
         brain_conn=None) -> RuntimeContext:
    return RuntimeContext(
        sql="SELECT 1",
        fingerprint=fingerprint,
        chart_winner=chart_winner,
        brain_conn=brain_conn,
    )


# ── run_consult ───────────────────────────────────────────────────────────────

class TestRunConsult:

    def test_no_op_when_brain_conn_is_none(self) -> None:
        ctx = _ctx()
        out = engine.run_consult(ctx)
        assert out.feedback_preferred is None

    def test_no_op_when_fingerprint_is_unknown(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        ctx = _ctx(fingerprint="UNKNOWN", brain_conn=brain)
        out = engine.run_consult(ctx)
        assert out.feedback_preferred is None

    def test_returns_none_when_no_pattern(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        ctx = _ctx(fingerprint="fp_new", brain_conn=brain)
        out = engine.run_consult(ctx)
        assert out.feedback_preferred is None

    def test_sets_feedback_preferred_from_brain(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        brain.execute(
            "INSERT INTO feedback_patterns VALUES ('fp1','chart_type','line','bar','2024-01-01')"
        )
        ctx = _ctx(fingerprint="fp1", brain_conn=brain)
        out = engine.run_consult(ctx)
        assert out.feedback_preferred == "bar"

    def test_different_fingerprints_stay_independent(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        brain.execute(
            "INSERT INTO feedback_patterns VALUES ('fpA','chart_type','line','bar','2024-01-01')"
        )
        ctx_a = _ctx(fingerprint="fpA", brain_conn=brain)
        ctx_b = _ctx(fingerprint="fpB", brain_conn=brain)
        assert engine.run_consult(ctx_a).feedback_preferred == "bar"
        assert engine.run_consult(ctx_b).feedback_preferred is None


# ── run_apply ─────────────────────────────────────────────────────────────────

class TestRunApply:

    def test_no_op_when_feedback_preferred_is_none(self) -> None:
        ctx = _ctx(chart_winner="line")
        ctx.feedback_preferred = None
        out = engine.run_apply(ctx)
        assert out.chart_winner == "line"

    def test_never_changes_winner_even_with_preference(self) -> None:
        ctx = _ctx(chart_winner="line")
        ctx.feedback_preferred = "bar"
        out = engine.run_apply(ctx)
        assert out.chart_winner == "line"  # engine inference unchanged

    def test_preferred_field_preserved_after_apply(self) -> None:
        ctx = _ctx(chart_winner="line")
        ctx.feedback_preferred = "bar"
        out = engine.run_apply(ctx)
        assert out.feedback_preferred == "bar"  # available for API to surface

    def test_no_op_with_candidates_present(self) -> None:
        from sqlviz_inference.context import ChartCandidate

        ctx = _ctx(chart_winner="line")
        ctx.feedback_preferred = "bar"
        ctx.chart_candidates = [
            ChartCandidate("line", 0.9, 0.0, 0.9, 0.9),
            ChartCandidate("bar", 0.7, 0.0, 0.7, 0.7),
        ]
        out = engine.run_apply(ctx)
        assert out.chart_winner == "line"  # never forced, even when bar is valid

    def test_no_op_when_preferred_not_in_candidates(self) -> None:
        from sqlviz_inference.context import ChartCandidate

        ctx = _ctx(chart_winner="line")
        ctx.feedback_preferred = "scatter"
        ctx.chart_candidates = [
            ChartCandidate("line", 0.9, 0.0, 0.9, 0.9),
            ChartCandidate("bar", 0.7, 0.0, 0.7, 0.7),
        ]
        out = engine.run_apply(ctx)
        assert out.chart_winner == "line"


# ── run_persist ───────────────────────────────────────────────────────────────

class TestRunPersist:

    def test_no_op_when_brain_conn_is_none(self) -> None:
        ctx = _ctx(chart_winner="bar")
        out = engine.run_persist(ctx)
        assert out.chart_winner == "bar"

    def test_no_op_when_fingerprint_is_unknown(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        ctx = _ctx(fingerprint="UNKNOWN", brain_conn=brain)
        engine.run_persist(ctx)
        count = brain.execute("SELECT COUNT(*) FROM feedback_events").fetchone()
        assert count is not None and count[0] == 0

    def test_logs_event_to_feedback_events(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        ctx = _ctx(fingerprint="fp1", chart_winner="bar", brain_conn=brain)
        engine.run_persist(ctx)
        count = brain.execute(
            "SELECT COUNT(*) FROM feedback_events WHERE fingerprint = 'fp1'"
        ).fetchone()
        assert count is not None and count[0] == 1

    def test_does_not_crash_when_brain_unavailable(self) -> None:
        ctx = _ctx(fingerprint="fp1", chart_winner="bar", brain_conn=None)
        engine.run_persist(ctx)  # must not raise


# ── Full round-trip ───────────────────────────────────────────────────────────

class TestRoundTrip:

    def test_consult_sets_preferred_winner_unchanged(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        brain.execute(
            "INSERT INTO feedback_patterns VALUES "
            "('fp_rt','chart_type','line','scatter','2024-01-01')"
        )
        ctx = _ctx(fingerprint="fp_rt", chart_winner="line", brain_conn=brain)
        ctx = engine.run_consult(ctx)
        assert ctx.feedback_preferred == "scatter"
        ctx = engine.run_apply(ctx)
        assert ctx.chart_winner == "line"  # engine inference never overridden

    def test_no_pattern_leaves_winner_unchanged(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        ctx = _ctx(fingerprint="fp_new", chart_winner="line", brain_conn=brain)
        ctx = engine.run_consult(ctx)
        ctx = engine.run_apply(ctx)
        assert ctx.chart_winner == "line"

    def test_persist_follows_apply(self, tmp_path: Path) -> None:
        brain = _brain(tmp_path)
        brain.execute(
            "INSERT INTO feedback_patterns VALUES "
            "('fp_p','chart_type','line','bar','2024-01-01')"
        )
        ctx = _ctx(fingerprint="fp_p", chart_winner="line", brain_conn=brain)
        ctx = engine.run_consult(ctx)
        ctx = engine.run_apply(ctx)
        assert ctx.chart_winner == "line"  # engine inference unchanged
        engine.run_persist(ctx)
        count = brain.execute(
            "SELECT COUNT(*) FROM feedback_events WHERE fingerprint = 'fp_p'"
        ).fetchone()
        assert count is not None and count[0] == 1
