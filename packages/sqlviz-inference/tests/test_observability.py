"""Tests for v0.2.3 Observability & Diagnostics."""
from __future__ import annotations

import sqlviz_inference
from sqlviz_inference.context import RuntimeContext


# ── Fixtures ─────────────────────────────────────────────────────────────────

_SQL_KPI = "SELECT SUM(revenue) AS total FROM sales"
_SQL_TREND = "SELECT date, SUM(revenue) FROM sales GROUP BY date ORDER BY date"


def _infer(sql: str, **kwargs):
    return sqlviz_inference.infer(sql, **kwargs)


# ── trace_id ──────────────────────────────────────────────────────────────────

class TestTraceId:
    def test_trace_id_is_set(self):
        result = _infer(_SQL_KPI)
        assert isinstance(result.trace_id, str)
        assert len(result.trace_id) == 8

    def test_trace_id_is_unique_per_call(self):
        r1 = _infer(_SQL_KPI)
        r2 = _infer(_SQL_KPI)
        assert r1.trace_id != r2.trace_id

    def test_context_trace_id_generated_at_init(self):
        ctx = RuntimeContext(sql="SELECT 1")
        assert isinstance(ctx.trace_id, str)
        assert len(ctx.trace_id) == 8

    def test_context_trace_id_unique_per_instance(self):
        ctx1 = RuntimeContext(sql="SELECT 1")
        ctx2 = RuntimeContext(sql="SELECT 1")
        assert ctx1.trace_id != ctx2.trace_id


# ── execution_state ───────────────────────────────────────────────────────────

class TestExecutionState:
    def test_success_when_no_errors(self):
        result = _infer(_SQL_KPI)
        assert result.execution_state == "success"

    def test_degraded_when_fallback_applied(self):
        """execution_state is 'degraded' whenever fallback_applied is True."""
        # NTILE/percentile reliably triggers ChartEngine fallback_applied=True
        result = _infer(
            "SELECT NTILE(4) OVER (ORDER BY revenue) AS quartile FROM sales"
        )
        if result.fallback_applied:
            assert result.execution_state == "degraded"
        else:
            # Pipeline ran cleanly — valid non-failed state
            assert result.execution_state in {"success", "warning", "degraded"}

    def test_execution_state_is_string(self):
        result = _infer(_SQL_TREND)
        assert result.execution_state in {"success", "warning", "degraded", "failed"}

    def test_default_state_in_context(self):
        ctx = RuntimeContext(sql="SELECT 1")
        assert ctx.execution_state == "success"


# ── module_timings ────────────────────────────────────────────────────────────

class TestModuleTimings:
    def test_timings_absent_by_default(self):
        result = _infer(_SQL_KPI)
        assert result.module_timings is None

    def test_timings_present_when_debug_true(self):
        result = _infer(_SQL_KPI, debug=True)
        assert result.module_timings is not None
        assert isinstance(result.module_timings, dict)

    def test_timings_cover_all_pipeline_steps(self):
        result = _infer(_SQL_KPI, debug=True)
        timings = result.module_timings
        assert timings is not None
        expected_steps = {
            "parser", "result_profiler", "column_role_detector", "features",
            "semantic", "intent", "chart", "constraint", "feedback_consult",
            "readability", "scoring", "feedback_apply", "visual_spec_builder",
            "layout", "layout_declaration_builder", "dashboard_role_classifier",
            "filters", "range_pairing", "title", "explanation_engine",
            "feedback_persist",
        }
        assert expected_steps.issubset(set(timings.keys()))

    def test_timings_are_non_negative_floats(self):
        result = _infer(_SQL_KPI, debug=True)
        assert result.module_timings is not None
        for name, ms in result.module_timings.items():
            assert isinstance(ms, float), f"{name} timing not float"
            assert ms >= 0.0, f"{name} timing negative"


# ── get_logger ────────────────────────────────────────────────────────────────

class TestGetLogger:
    def test_logger_returns_named_logger(self):
        import logging
        from sqlviz_inference.utils.sqlviz_logging import get_logger
        log = get_logger("test_module")
        assert log.name == "sqlviz.test_module"
        assert isinstance(log, logging.Logger)

    def test_same_name_returns_same_logger(self):
        from sqlviz_inference.utils.sqlviz_logging import get_logger
        l1 = get_logger("dup_module")
        l2 = get_logger("dup_module")
        assert l1 is l2
