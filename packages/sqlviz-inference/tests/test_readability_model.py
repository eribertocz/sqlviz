"""Tests for ReadabilityModel — V0.2 Fase C.

Each concept has ≥ 2 positive cases (penalty fires) and ≥ 2 negative cases
(no penalty, chart survives with base score).
"""
from __future__ import annotations

import pytest
from sqlviz_inference.context import ChartCandidate, RuntimeContext
from sqlviz_inference.contracts.column_roles import ColumnRole, ColumnRoles
from sqlviz_inference.contracts.constraint import ConstraintReport, ConstraintViolation
from sqlviz_inference.profile.data_profile import ColumnProfile, DataProfile
from sqlviz_inference.readability.readability_model import ReadabilityModel

model = ReadabilityModel()

_V0_CHARTS = ["kpi", "line", "bar", "bar_horizontal", "pie", "scatter", "histogram", "table"]


def _candidate(ct: str, score: float = 1.0) -> ChartCandidate:
    return ChartCandidate(
        chart_type=ct,
        affinity_score=score,
        penalty_total=0.0,
        final_score=score,
        normalized_score=score,
    )


def _col_profile(
    name: str,
    cardinality: int,
    max_label_length: int,
    is_numeric: bool = False,
) -> ColumnProfile:
    return ColumnProfile(
        name=name,
        type="VARCHAR" if not is_numeric else "DOUBLE",
        cardinality=cardinality,
        null_count=0,
        null_fraction=0.0,
        max_label_length=max_label_length,
        mean_label_length=float(max_label_length),
        is_numeric=is_numeric,
    )


def _ctx(
    charts: list[str],
    row_count: int = 5,
    cat_cardinality: int = 3,
    max_label_len: int = 6,
    n_metric: int = 1,
    eliminated: list[str] | None = None,
    sql: str = "SELECT x FROM t",
) -> RuntimeContext:
    candidates = [_candidate(ct) for ct in charts]
    col_profiles = [
        _col_profile("cat_col", cat_cardinality, max_label_len, is_numeric=False),
    ] + [
        _col_profile(f"metric_{i}", 1, 5, is_numeric=True) for i in range(n_metric)
    ]
    profile = DataProfile(
        row_count=row_count,
        col_count=len(col_profiles),
        single_row=(row_count == 1),
        wide_table=False,
        column_profiles=col_profiles,
    )
    metric_roles = [ColumnRole(f"metric_{i}", "metric") for i in range(n_metric)]
    roles = ColumnRoles(roles=[ColumnRole("cat_col", "category")] + metric_roles)

    constraint_report = None
    if eliminated:
        viols = [
            ConstraintViolation(ct, "test_rule", "hard", "test") for ct in eliminated
        ]
        constraint_report = ConstraintReport(eliminated=viols, rules_checked=1)

    return RuntimeContext(
        sql=sql,
        chart_candidates=candidates,
        chart_winner=charts[0],
        data_profile=profile,
        column_roles=roles,
        constraint_report=constraint_report,
    )


def _get(result, chart_type: str):
    """Return CandidateReadability for the given chart_type."""
    return next(c for c in result.by_candidate if c.chart_type == chart_type)


# ── Legibility — bar ───────────────────────────────────────────────────────


class TestLegibilityBar:

    def test_bar_many_categories_penalizes(self) -> None:
        ctx = _ctx(["bar"], cat_cardinality=10)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        # excess=5, penalty=0.04*5=0.20, base=0.92 → 0.72
        assert r.legibility_score < 0.92

    def test_bar_very_many_categories_heavy_penalty(self) -> None:
        ctx = _ctx(["bar"], cat_cardinality=15)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        # excess=10, penalty=0.04*10=0.40, base=0.92 → 0.52
        assert r.legibility_score < 0.75

    def test_bar_few_categories_no_penalty(self) -> None:
        ctx = _ctx(["bar"], cat_cardinality=3)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        assert r.legibility_score == pytest.approx(0.92, abs=0.01)

    def test_bar_exactly_5_categories_no_penalty(self) -> None:
        ctx = _ctx(["bar"], cat_cardinality=5)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        # excess = max(0, 5-5) = 0
        assert r.legibility_score == pytest.approx(0.92, abs=0.01)

    def test_bar_long_labels_penalizes(self) -> None:
        ctx = _ctx(["bar"], max_label_len=11, cat_cardinality=3)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        # max_label_len > 10 → -0.08
        assert r.legibility_score == pytest.approx(0.92 - 0.08, abs=0.01)

    def test_bar_medium_labels_smaller_penalty(self) -> None:
        ctx = _ctx(["bar"], max_label_len=8, cat_cardinality=3)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        # max_label_len > 7 → -0.04
        assert r.legibility_score == pytest.approx(0.92 - 0.04, abs=0.01)

    def test_bar_short_labels_no_label_penalty(self) -> None:
        ctx = _ctx(["bar"], max_label_len=5, cat_cardinality=3)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        assert r.legibility_score == pytest.approx(0.92, abs=0.01)


# ── Legibility — pie ───────────────────────────────────────────────────────


class TestLegibilityPie:

    def test_pie_many_slices_penalizes(self) -> None:
        ctx = _ctx(["pie"], cat_cardinality=6)
        result = model.run(ctx).readability_result
        r = _get(result, "pie")
        # excess=4, penalty=0.06*4=0.24, base=0.88 → 0.64
        assert r.legibility_score == pytest.approx(0.88 - 0.24, abs=0.01)

    def test_pie_very_many_slices_penalizes_further(self) -> None:
        ctx = _ctx(["pie"], cat_cardinality=9)
        result = model.run(ctx).readability_result
        r = _get(result, "pie")
        # excess=7, penalty=0.06*7=0.42, base=0.88 → clamped to 0.10
        assert r.legibility_score >= 0.10
        assert r.legibility_score < 0.50

    def test_pie_two_slices_no_penalty(self) -> None:
        ctx = _ctx(["pie"], cat_cardinality=2)
        result = model.run(ctx).readability_result
        r = _get(result, "pie")
        assert r.legibility_score == pytest.approx(0.88, abs=0.01)

    def test_pie_three_slices_small_penalty(self) -> None:
        ctx = _ctx(["pie"], cat_cardinality=3)
        result = model.run(ctx).readability_result
        r = _get(result, "pie")
        # excess=1, penalty=0.06
        assert r.legibility_score == pytest.approx(0.88 - 0.06, abs=0.01)


# ── Legibility — line ──────────────────────────────────────────────────────


class TestLegibilityLine:

    def test_line_multiple_series_penalizes(self) -> None:
        ctx = _ctx(["line"], n_metric=4)
        result = model.run(ctx).readability_result
        r = _get(result, "line")
        # series_excess=3, penalty=0.05*3=0.15, base=0.93 → 0.78
        assert r.legibility_score == pytest.approx(0.93 - 0.15, abs=0.01)

    def test_line_dense_rows_penalizes(self) -> None:
        ctx = _ctx(["line"], row_count=60, n_metric=1)
        result = model.run(ctx).readability_result
        r = _get(result, "line")
        # row_count > 50 → -0.04
        assert r.legibility_score == pytest.approx(0.93 - 0.04, abs=0.01)

    def test_line_single_series_no_penalty(self) -> None:
        ctx = _ctx(["line"], n_metric=1, row_count=10)
        result = model.run(ctx).readability_result
        r = _get(result, "line")
        assert r.legibility_score == pytest.approx(0.93, abs=0.01)

    def test_line_two_series_moderate_penalty(self) -> None:
        ctx = _ctx(["line"], n_metric=2, row_count=10)
        result = model.run(ctx).readability_result
        r = _get(result, "line")
        # series_excess=1, penalty=0.05
        assert r.legibility_score == pytest.approx(0.93 - 0.05, abs=0.01)


# ── Legibility — scatter ───────────────────────────────────────────────────


class TestLegibilityScatter:

    def test_scatter_overplotting_heavy(self) -> None:
        ctx = _ctx(["scatter"], row_count=150)
        result = model.run(ctx).readability_result
        r = _get(result, "scatter")
        # row_count > 100 → -0.06
        assert r.legibility_score == pytest.approx(0.82 - 0.06, abs=0.01)

    def test_scatter_moderate_density_small_penalty(self) -> None:
        ctx = _ctx(["scatter"], row_count=60)
        result = model.run(ctx).readability_result
        r = _get(result, "scatter")
        # row_count > 50 → -0.03
        assert r.legibility_score == pytest.approx(0.82 - 0.03, abs=0.01)

    def test_scatter_few_rows_no_penalty(self) -> None:
        ctx = _ctx(["scatter"], row_count=30)
        result = model.run(ctx).readability_result
        r = _get(result, "scatter")
        assert r.legibility_score == pytest.approx(0.82, abs=0.01)


# ── Legibility — table ────────────────────────────────────────────────────


class TestLegibilityTable:

    def test_table_many_rows_penalizes(self) -> None:
        ctx = _ctx(["table"], row_count=30)
        result = model.run(ctx).readability_result
        r = _get(result, "table")
        # row_excess=20, steps=4, penalty=0.02*4=0.08
        assert r.legibility_score < 0.78

    def test_table_few_rows_no_row_penalty(self) -> None:
        ctx = _ctx(["table"], row_count=8)
        result = model.run(ctx).readability_result
        r = _get(result, "table")
        # row_excess = max(0, 8-10) = 0 → no row penalty
        assert r.legibility_score == pytest.approx(0.78, abs=0.05)

    def test_legibility_clamped_above_zero_one(self) -> None:
        # Extreme case must stay in [0.10, 1.00]
        ctx = _ctx(["bar"], cat_cardinality=40, max_label_len=15)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        assert 0.10 <= r.legibility_score <= 1.00


# ── col_span ──────────────────────────────────────────────────────────────


class TestColSpan:

    def test_kpi_always_narrow(self) -> None:
        ctx = _ctx(["kpi"])
        result = model.run(ctx).readability_result
        r = _get(result, "kpi")
        assert r.col_span_min == 2
        assert r.col_span_preferred == 3
        assert r.col_span_max == 4

    def test_table_always_wide(self) -> None:
        ctx = _ctx(["table"])
        result = model.run(ctx).readability_result
        r = _get(result, "table")
        assert r.col_span_min == 8
        assert r.col_span_preferred == 12

    def test_bar_high_cardinality_widens(self) -> None:
        ctx = _ctx(["bar"], cat_cardinality=12)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        assert r.col_span_min >= 8
        assert r.col_span_preferred >= 10

    def test_bar_long_labels_widens_preferred(self) -> None:
        ctx = _ctx(["bar"], max_label_len=10, cat_cardinality=3)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        # max_label_len > 8 → preferred + 2
        assert r.col_span_preferred >= 8

    def test_bar_normal_cardinality_default_span(self) -> None:
        ctx = _ctx(["bar"], cat_cardinality=4, max_label_len=5)
        result = model.run(ctx).readability_result
        r = _get(result, "bar")
        assert r.col_span_preferred == 6


# ── height ────────────────────────────────────────────────────────────────


class TestHeight:

    def test_kpi_fixed_height(self) -> None:
        ctx = _ctx(["kpi"])
        result = model.run(ctx).readability_result
        r = _get(result, "kpi")
        assert r.height_px_recommended == 180

    def test_bar_horizontal_grows_with_cardinality(self) -> None:
        ctx = _ctx(["bar_horizontal"], cat_cardinality=8)
        result = model.run(ctx).readability_result
        r = _get(result, "bar_horizontal")
        # 80 + 8*32 = 336
        assert r.height_px_recommended == 80 + 8 * 32

    def test_bar_horizontal_capped_at_600(self) -> None:
        ctx = _ctx(["bar_horizontal"], cat_cardinality=25)
        result = model.run(ctx).readability_result
        r = _get(result, "bar_horizontal")
        assert r.height_px_recommended == 600

    def test_bar_horizontal_minimum_200(self) -> None:
        ctx = _ctx(["bar_horizontal"], cat_cardinality=1)
        result = model.run(ctx).readability_result
        r = _get(result, "bar_horizontal")
        assert r.height_px_recommended == 200

    def test_table_grows_with_rows(self) -> None:
        ctx = _ctx(["table"], row_count=10)
        result = model.run(ctx).readability_result
        r = _get(result, "table")
        # 120 + 10*28 = 400
        assert r.height_px_recommended == 400

    def test_table_capped_at_600(self) -> None:
        ctx = _ctx(["table"], row_count=50)
        result = model.run(ctx).readability_result
        r = _get(result, "table")
        assert r.height_px_recommended == 600

    def test_table_minimum_240(self) -> None:
        ctx = _ctx(["table"], row_count=1)
        result = model.run(ctx).readability_result
        r = _get(result, "table")
        assert r.height_px_recommended == 240


# ── Eliminated candidates skipped ────────────────────────────────────────


class TestElimination:

    def test_eliminated_chart_not_in_readability(self) -> None:
        ctx = _ctx(["bar", "pie", "line"], eliminated=["pie"])
        result = model.run(ctx).readability_result
        types = {c.chart_type for c in result.by_candidate}
        assert "pie" not in types
        assert "bar" in types
        assert "line" in types

    def test_non_eliminated_charts_scored(self) -> None:
        ctx = _ctx(["bar", "scatter"], eliminated=["bar"])
        result = model.run(ctx).readability_result
        types = {c.chart_type for c in result.by_candidate}
        assert "scatter" in types
        assert "bar" not in types

    def test_no_elimination_all_scored(self) -> None:
        ctx = _ctx(["bar", "line", "kpi"])
        result = model.run(ctx).readability_result
        assert len(result.by_candidate) == 3

    def test_readability_result_written_to_context(self) -> None:
        ctx = _ctx(["bar"])
        out = model.run(ctx)
        assert out.readability_result is not None
        assert len(out.readability_result.by_candidate) == 1
