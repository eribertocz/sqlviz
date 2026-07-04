"""Dashboard Engine tests — DOC5 Section 15.6."""
from __future__ import annotations

from sqlviz_inference.dashboard.dashboard_engine import DashboardEngine
from sqlviz_inference.result import InferenceResult


def make_result(chart_winner: str, intent_winner: str, col_span: int) -> InferenceResult:
    """Minimal InferenceResult for dashboard composition tests."""
    return InferenceResult(
        rules_version="test",
        feature_vector_version="v0",
        engine_version="test",
        intent_winner=intent_winner,
        intent_raw_score=0.9,
        intent_normalized_score=1.0,
        intent_confidence_gap=0.5,
        intent_quality="high",
        intent_alternatives=[],
        chart_winner=chart_winner,
        chart_raw_score=0.9,
        chart_normalized_score=1.0,
        chart_confidence_gap=0.5,
        chart_quality="high",
        chart_alternatives=[],
        col_span=col_span,
        row_span=1,
        layout_importance=0.5,
        panel_height_px=360,
        trend_direction_label="unknown",
        filter_controls=[],
        title="Test",
        title_confidence=0.8,
        fallback_applied=False,
        fallback_reason="",
        explanation=[],
        score_trace={},
        fingerprint="TEST",
        feature_vector=[0.0] * 39,
        errors=[],
        elapsed_ms=0.0,
    )


engine = DashboardEngine()


class TestKPIGrouping:

    def test_single_kpi_centered(self) -> None:
        panels = [("p1", make_result("kpi", "kpi", 3))]
        layout = engine.compose(panels)
        panel = layout.rows[0].panels[0]
        assert panel.final_col_span == 4
        assert panel.col_offset == 4

    def test_two_kpis_share_row(self) -> None:
        panels = [
            ("p1", make_result("kpi", "kpi", 3)),
            ("p2", make_result("kpi", "kpi", 3)),
        ]
        layout = engine.compose(panels)
        assert len(layout.rows[0].panels) == 2
        assert layout.rows[0].panels[0].final_col_span == 4
        assert layout.rows[0].panels[0].col_offset == 2
        assert layout.rows[0].panels[1].col_offset == 0

    def test_three_kpis_col_span_4(self) -> None:
        panels = [("p%d" % i, make_result("kpi", "kpi", 3)) for i in range(3)]
        layout = engine.compose(panels)
        assert len(layout.rows[0].panels) == 3
        assert layout.rows[0].panels[0].final_col_span == 4

    def test_four_kpis_one_row(self) -> None:
        panels = [("p%d" % i, make_result("kpi", "kpi", 3)) for i in range(4)]
        layout = engine.compose(panels)
        assert len(layout.rows[0].panels) == 4
        assert layout.rows[0].panels[0].final_col_span == 3

    def test_five_kpis_wrap_to_two_rows(self) -> None:
        panels = [("p%d" % i, make_result("kpi", "kpi", 3)) for i in range(5)]
        layout = engine.compose(panels)
        kpi_rows = [
            r for r in layout.rows
            if r.panels[0].inference_result.chart_winner == "kpi"
        ]
        assert len(kpi_rows) == 2


class TestNarrativeOrdering:

    def test_trend_before_comparison(self) -> None:
        panels = [
            ("p1", make_result("bar", "comparison", 12)),
            ("p2", make_result("line", "trend", 12)),
        ]
        layout = engine.compose(panels)
        first_intent = layout.rows[0].panels[0].inference_result.intent_winner
        assert first_intent == "trend"

    def test_detail_always_last(self) -> None:
        panels = [
            ("p1", make_result("table", "detail", 12)),
            ("p2", make_result("line", "trend", 12)),
            ("p3", make_result("bar", "comparison", 12)),
        ]
        layout = engine.compose(panels)
        last_intent = layout.rows[-1].panels[0].inference_result.intent_winner
        assert last_intent == "detail"

    def test_kpi_rows_before_non_kpi(self) -> None:
        panels = [
            ("p1", make_result("line", "trend", 12)),
            ("p2", make_result("kpi", "kpi", 3)),
        ]
        layout = engine.compose(panels)
        first_chart = layout.rows[0].panels[0].inference_result.chart_winner
        assert first_chart == "kpi"


class TestRowPacking:

    def test_full_width_never_shares_row(self) -> None:
        panels = [("p1", make_result("line", "trend", 12))]
        layout = engine.compose(panels)
        assert len(layout.rows[0].panels) == 1

    def test_kpi_and_full_width_in_separate_rows(self) -> None:
        panels = [
            ("p1", make_result("kpi", "kpi", 3)),
            ("p2", make_result("line", "trend", 12)),
        ]
        layout = engine.compose(panels)
        assert layout.panel_count == 2
        assert len(layout.rows) == 2  # KPI row + Line row

    def test_panels_that_fit_share_row(self) -> None:
        panels = [
            ("p1", make_result("bar", "comparison", 8)),
            ("p2", make_result("pie", "composition", 4)),
        ]
        layout = engine.compose(panels)
        # 8 + 4 = 12, should pack into a single row
        assert layout.panel_count == 2
        # comparison (priority 2) before composition (priority 4)
        shared_row = next(r for r in layout.rows if len(r.panels) == 2)
        assert shared_row.total_span == 12

    def test_overflow_starts_new_row(self) -> None:
        panels = [
            ("p1", make_result("bar", "comparison", 8)),
            ("p2", make_result("bar", "comparison", 8)),
        ]
        layout = engine.compose(panels)
        # 8 + 8 = 16 > 12, must split into two rows
        assert len(layout.rows) == 2

    def test_row_index_assigned(self) -> None:
        panels = [
            ("p1", make_result("kpi", "kpi", 3)),
            ("p2", make_result("line", "trend", 12)),
        ]
        layout = engine.compose(panels)
        kpi_panel = layout.rows[0].panels[0]
        line_panel = layout.rows[1].panels[0]
        assert kpi_panel.row_index == 0
        assert line_panel.row_index == 1


class TestEmptyAndSingle:

    def test_empty_panels_list(self) -> None:
        layout = engine.compose([])
        assert layout.rows == []
        assert layout.panel_count == 0

    def test_single_non_kpi_panel(self) -> None:
        panels = [("p1", make_result("table", "detail", 12))]
        layout = engine.compose(panels)
        assert layout.panel_count == 1

    def test_panel_count_matches_input(self) -> None:
        panels = [
            ("p1", make_result("kpi", "kpi", 3)),
            ("p2", make_result("line", "trend", 12)),
            ("p3", make_result("bar", "comparison", 12)),
            ("p4", make_result("kpi", "kpi", 3)),
        ]
        layout = engine.compose(panels)
        assert layout.panel_count == 4
