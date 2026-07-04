"""KPI Shelf v0.1 protector tests — all 8 row-size cases + 9/12 KPI cases.

See DOC5 §16.34 for the rule specification.

Shelf table:
    row size 1 → span=4, offset=4  (centered: 4+KPI+4)
    row size 2 → span=4, offset=2  (centered: 2+KPI+KPI+2)
    row size 3 → span=4, offset=0  (fills 12: 4+4+4)
    row size 4 → span=3, offset=0  (fills 12: 3+3+3+3)
    5+ → first row takes 4 KPIs (span=3), remainder follows same rules
"""
from __future__ import annotations

from sqlviz_inference.dashboard.dashboard_engine import DashboardEngine, DashboardRow
from sqlviz_inference.result import InferenceResult

engine = DashboardEngine()


def _kpi(n: int) -> list[tuple[str, InferenceResult]]:
    """Return n KPI panels for compose()."""
    dummy = InferenceResult(
        rules_version="test",
        feature_vector_version="v0",
        engine_version="test",
        intent_winner="kpi",
        intent_raw_score=0.9,
        intent_normalized_score=1.0,
        intent_confidence_gap=0.5,
        intent_quality="high",
        intent_alternatives=[],
        chart_winner="kpi",
        chart_raw_score=0.9,
        chart_normalized_score=1.0,
        chart_confidence_gap=0.5,
        chart_quality="high",
        chart_alternatives=[],
        col_span=3,
        row_span=1,
        layout_importance=0.5,
        panel_height_px=120,
        trend_direction_label="unknown",
        filter_controls=[],
        title="KPI",
        title_confidence=0.8,
        fallback_applied=False,
        fallback_reason="",
        explanation=[],
        score_trace={},
        fingerprint="KPI",
        feature_vector=[0.0] * 39,
        errors=[],
        elapsed_ms=0.0,
    )
    return [(f"k{i}", dummy) for i in range(n)]


def _kpi_rows(n: int) -> list[DashboardRow]:
    layout = engine.compose(_kpi(n))
    return [r for r in layout.rows if r.panels[0].inference_result.chart_winner == "kpi"]


class TestKPIShelf:
    """Protects KPI Shelf v0.1 centering rule for all 8 row-size cases + overflow."""

    # ── Case 1: 1 KPI → span=4, offset=4 ────────────────────────────────────

    def test_case_1_kpi_span(self) -> None:
        rows = _kpi_rows(1)
        assert rows[0].panels[0].final_col_span == 4

    def test_case_1_kpi_offset(self) -> None:
        rows = _kpi_rows(1)
        assert rows[0].panels[0].col_offset == 4

    # ── Case 2: 2 KPIs → span=4 each, offset=2 on first ─────────────────────

    def test_case_2_kpi_span(self) -> None:
        rows = _kpi_rows(2)
        assert all(p.final_col_span == 4 for p in rows[0].panels)

    def test_case_2_kpi_offset_first(self) -> None:
        rows = _kpi_rows(2)
        assert rows[0].panels[0].col_offset == 2

    def test_case_2_kpi_offset_second(self) -> None:
        rows = _kpi_rows(2)
        assert rows[0].panels[1].col_offset == 0

    def test_case_2_kpi_total_span(self) -> None:
        rows = _kpi_rows(2)
        assert rows[0].total_span == 8

    # ── Case 3: 3 KPIs → span=4 each, offset=0 ───────────────────────────────

    def test_case_3_kpi_span(self) -> None:
        rows = _kpi_rows(3)
        assert all(p.final_col_span == 4 for p in rows[0].panels)

    def test_case_3_kpi_offset(self) -> None:
        rows = _kpi_rows(3)
        assert rows[0].panels[0].col_offset == 0

    def test_case_3_kpi_total_span(self) -> None:
        rows = _kpi_rows(3)
        assert rows[0].total_span == 12

    # ── Case 4: 4 KPIs → span=3 each, offset=0 ───────────────────────────────

    def test_case_4_kpi_span(self) -> None:
        rows = _kpi_rows(4)
        assert all(p.final_col_span == 3 for p in rows[0].panels)

    def test_case_4_kpi_offset(self) -> None:
        rows = _kpi_rows(4)
        assert rows[0].panels[0].col_offset == 0

    def test_case_4_kpi_total_span(self) -> None:
        rows = _kpi_rows(4)
        assert rows[0].total_span == 12

    # ── Case 5: 5 KPIs → row0: 4×span3, row1: 1×span4/offset4 ───────────────

    def test_case_5_two_kpi_rows(self) -> None:
        rows = _kpi_rows(5)
        assert len(rows) == 2

    def test_case_5_first_row_four_panels(self) -> None:
        rows = _kpi_rows(5)
        assert len(rows[0].panels) == 4

    def test_case_5_first_row_span(self) -> None:
        rows = _kpi_rows(5)
        assert all(p.final_col_span == 3 for p in rows[0].panels)

    def test_case_5_second_row_span(self) -> None:
        rows = _kpi_rows(5)
        assert rows[1].panels[0].final_col_span == 4

    def test_case_5_second_row_offset(self) -> None:
        rows = _kpi_rows(5)
        assert rows[1].panels[0].col_offset == 4

    # ── Case 6: 6 KPIs → row0: 4×span3, row1: 2×span4/offset2 ───────────────

    def test_case_6_second_row_span(self) -> None:
        rows = _kpi_rows(6)
        assert all(p.final_col_span == 4 for p in rows[1].panels)

    def test_case_6_second_row_offset(self) -> None:
        rows = _kpi_rows(6)
        assert rows[1].panels[0].col_offset == 2

    def test_case_6_second_row_count(self) -> None:
        rows = _kpi_rows(6)
        assert len(rows[1].panels) == 2

    # ── Case 7: 7 KPIs → row0: 4×span3, row1: 3×span4/offset0 ───────────────

    def test_case_7_second_row_span(self) -> None:
        rows = _kpi_rows(7)
        assert all(p.final_col_span == 4 for p in rows[1].panels)

    def test_case_7_second_row_offset(self) -> None:
        rows = _kpi_rows(7)
        assert rows[1].panels[0].col_offset == 0

    def test_case_7_second_row_count(self) -> None:
        rows = _kpi_rows(7)
        assert len(rows[1].panels) == 3

    # ── Case 8: 8 KPIs → 2 rows of 4, both span=3/offset=0 ──────────────────

    def test_case_8_two_full_rows(self) -> None:
        rows = _kpi_rows(8)
        assert len(rows) == 2
        for row in rows:
            assert len(row.panels) == 4
            assert all(p.final_col_span == 3 for p in row.panels)
            assert row.panels[0].col_offset == 0

    # ── 9+ KPIs: continue 4-per-row pattern ──────────────────────────────────

    def test_9_kpis_three_rows(self) -> None:
        rows = _kpi_rows(9)
        assert len(rows) == 3

    def test_9_kpis_third_row_span_and_offset(self) -> None:
        rows = _kpi_rows(9)
        assert rows[2].panels[0].final_col_span == 4
        assert rows[2].panels[0].col_offset == 4

    def test_12_kpis_three_full_rows(self) -> None:
        rows = _kpi_rows(12)
        assert len(rows) == 3
        for row in rows:
            assert all(p.final_col_span == 3 for p in row.panels)
            assert row.total_span == 12
