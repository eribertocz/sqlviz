"""Tests for LayoutDeclarationBuilder — V0.2 Fase D.

Each concept: ≥ 2 positive cases (rule fires) + ≥ 2 negative/fallback cases.
"""
from __future__ import annotations

from sqlviz_inference.context import ChartCandidate, RuntimeContext
from sqlviz_inference.contracts.readability import CandidateReadability, ReadabilityResult
from sqlviz_inference.layout.layout_declaration_builder import LayoutDeclarationBuilder

builder = LayoutDeclarationBuilder()


def _candidate(ct: str) -> ChartCandidate:
    return ChartCandidate(
        chart_type=ct, affinity_score=1.0, penalty_total=0.0,
        final_score=1.0, normalized_score=1.0,
    )


def _readability(chart_type: str, col_min: int, col_pref: int, col_max: int, height: int):
    return ReadabilityResult(by_candidate=[
        CandidateReadability(
            chart_type=chart_type,
            col_span_min=col_min,
            col_span_preferred=col_pref,
            col_span_max=col_max,
            height_px_recommended=height,
        )
    ])


def _ctx(
    chart_winner: str,
    readability_result: ReadabilityResult | None = None,
) -> RuntimeContext:
    return RuntimeContext(
        sql="SELECT x FROM t",
        chart_candidates=[_candidate(chart_winner)],
        chart_winner=chart_winner,
        readability_result=readability_result,
    )


class TestLayoutDeclarationFromReadability:

    def test_uses_readability_col_span_when_available(self) -> None:
        ctx = _ctx("bar", _readability("bar", 6, 10, 12, 400))
        out = builder.run(ctx)
        assert out.layout_declaration is not None
        assert out.layout_declaration.col_span_preferred == 10

    def test_uses_readability_height_when_available(self) -> None:
        ctx = _ctx("bar_horizontal", _readability("bar_horizontal", 4, 6, 12, 480))
        out = builder.run(ctx)
        assert out.layout_declaration.height_px_preferred == 480

    def test_height_bounds_from_preferred(self) -> None:
        ctx = _ctx("line", _readability("line", 8, 12, 12, 360))
        out = builder.run(ctx)
        decl = out.layout_declaration
        # h_min = max(120, int(360 * 0.70)) = 252
        # h_max = min(720, int(360 * 1.40)) = 504
        assert decl.height_px_min <= decl.height_px_preferred
        assert decl.height_px_preferred <= decl.height_px_max
        assert decl.height_px_min >= 120
        assert decl.height_px_max <= 720

    def test_col_span_hard_limits_enforced(self) -> None:
        # ReadabilityModel could return out-of-range values — clamp them
        ctx = _ctx("kpi", _readability("kpi", 1, 2, 15, 180))
        out = builder.run(ctx)
        decl = out.layout_declaration
        assert decl.col_span_min >= 3
        assert decl.col_span_max <= 12


class TestLayoutDeclarationFallback:

    def test_fallback_kpi_narrow(self) -> None:
        ctx = _ctx("kpi")  # no readability
        out = builder.run(ctx)
        decl = out.layout_declaration
        assert decl is not None
        assert decl.col_span_preferred <= 4
        assert decl.col_span_max <= 4

    def test_fallback_table_wide(self) -> None:
        ctx = _ctx("table")
        out = builder.run(ctx)
        decl = out.layout_declaration
        assert decl.col_span_preferred >= 12

    def test_fallback_line_wide(self) -> None:
        ctx = _ctx("line")
        out = builder.run(ctx)
        decl = out.layout_declaration
        assert decl.col_span_preferred >= 10

    def test_fallback_pie_medium(self) -> None:
        ctx = _ctx("pie")
        out = builder.run(ctx)
        decl = out.layout_declaration
        assert 4 <= decl.col_span_preferred <= 8

    def test_unknown_chart_type_gets_default(self) -> None:
        ctx = _ctx("funnel")
        out = builder.run(ctx)
        assert out.layout_declaration is not None
        # default fallback: col_span_preferred = 6
        assert out.layout_declaration.col_span_preferred == 6

    def test_fallback_when_readability_missing_chart_type(self) -> None:
        # ReadabilityResult exists but doesn't include the winner's chart type
        ctx = _ctx("scatter", _readability("bar", 6, 8, 12, 300))
        out = builder.run(ctx)
        # Should fall back to scatter's built-in defaults
        decl = out.layout_declaration
        assert decl is not None
        assert decl.col_span_preferred == 8  # scatter fallback


class TestLayoutDeclarationConstraints:

    def test_col_span_min_le_preferred_le_max(self) -> None:
        charts = ["kpi", "line", "bar", "bar_horizontal", "pie", "scatter", "histogram", "table"]
        for chart in charts:
            ctx = _ctx(chart)
            decl = builder.run(ctx).layout_declaration
            assert decl.col_span_min <= decl.col_span_preferred
            assert decl.col_span_preferred <= decl.col_span_max

    def test_height_min_le_preferred_le_max(self) -> None:
        for chart in ["kpi", "line", "bar", "table"]:
            ctx = _ctx(chart)
            decl = builder.run(ctx).layout_declaration
            assert decl.height_px_min <= decl.height_px_preferred
            assert decl.height_px_preferred <= decl.height_px_max

    def test_declaration_written_to_context(self) -> None:
        ctx = _ctx("bar")
        out = builder.run(ctx)
        assert out.layout_declaration is not None
