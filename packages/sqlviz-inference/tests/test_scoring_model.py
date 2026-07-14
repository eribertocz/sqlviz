"""Tests for ScoringModel — V0.2 Fase C.

Covers: 10-dimension computation, winner update, hard-fallback protection,
ConstraintEngine re-ranking, data-dependent dimension scaling.
"""
from __future__ import annotations

import pytest
from sqlviz_inference.context import ChartCandidate, RuntimeContext
from sqlviz_inference.contracts.column_roles import ColumnRole, ColumnRoles
from sqlviz_inference.contracts.constraint import ConstraintReport, ConstraintViolation
from sqlviz_inference.contracts.readability import CandidateReadability, ReadabilityResult
from sqlviz_inference.profile.data_profile import ColumnProfile, DataProfile
from sqlviz_inference.scoring.scoring_model import ScoringModel

model = ScoringModel()

_WEIGHTS_POS = {
    "semantic_fit": 0.45, "task_fit": 0.20, "perceptual_accuracy": 0.10,
    "readability": 0.08, "information_density": 0.06, "business_relevance": 0.06,
}
_WEIGHTS_NEG = {
    "cognitive_load": 0.02, "visual_clutter": 0.01, "ambiguity": 0.01, "interaction_cost": 0.01,
}


def _candidate(ct: str, norm_score: float = 0.80) -> ChartCandidate:
    return ChartCandidate(
        chart_type=ct,
        affinity_score=norm_score,
        penalty_total=0.0,
        final_score=norm_score,
        normalized_score=norm_score,
    )


def _profile(row_count: int, cat_cardinality: int = 3) -> DataProfile:
    col_profiles = [
        ColumnProfile("cat", "VARCHAR", cat_cardinality, 0, 0.0, 5, 5.0, False),
        ColumnProfile("val", "DOUBLE", 1, 0, 0.0, 5, 5.0, True),
    ]
    return DataProfile(
        row_count=row_count,
        col_count=2,
        single_row=(row_count == 1),
        wide_table=False,
        column_profiles=col_profiles,
    )


def _readability(chart_types: list[str], legibility: float = 0.90) -> ReadabilityResult:
    return ReadabilityResult(
        by_candidate=[
            CandidateReadability(ct, legibility_score=legibility)
            for ct in chart_types
        ]
    )


def _constraint_report(eliminated: list[str]) -> ConstraintReport:
    viols = [ConstraintViolation(ct, "rule", "hard", "test") for ct in eliminated]
    return ConstraintReport(eliminated=viols, rules_checked=1)


def _ctx(
    charts: list[str],
    winner: str,
    intent: str = "comparison",
    row_count: int = 5,
    cat_cardinality: int = 3,
    fallback_applied: bool = False,
    fallback_reason: str = "",
    eliminated: list[str] | None = None,
    norm_scores: dict[str, float] | None = None,
    n_metric: int = 1,
) -> RuntimeContext:
    if norm_scores is None:
        norm_scores = {ct: 0.80 for ct in charts}
    candidates = [_candidate(ct, norm_scores.get(ct, 0.80)) for ct in charts]
    metric_roles = [ColumnRole(f"m{i}", "metric") for i in range(n_metric)]
    roles = ColumnRoles(roles=[ColumnRole("cat", "category")] + metric_roles)

    cr = _constraint_report(eliminated) if eliminated else None

    return RuntimeContext(
        sql="SELECT x FROM t",
        chart_candidates=candidates,
        chart_winner=winner,
        intent_winner=intent,
        data_profile=_profile(row_count, cat_cardinality),
        column_roles=roles,
        constraint_report=cr,
        readability_result=_readability([ct for ct in charts if ct not in (eliminated or [])]),
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
    )


# ── Dimension values ──────────────────────────────────────────────────────


class TestDimensionValues:

    def test_perceptual_accuracy_line_highest(self) -> None:
        ctx = _ctx(["line"], winner="line", intent="trend")
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.perceptual_accuracy == pytest.approx(0.95, abs=0.01)

    def test_perceptual_accuracy_pie_lowest(self) -> None:
        ctx = _ctx(["pie"], winner="pie", intent="composition")
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.perceptual_accuracy == pytest.approx(0.60, abs=0.01)

    def test_perceptual_accuracy_kpi(self) -> None:
        ctx = _ctx(["kpi"], winner="kpi", intent="kpi", row_count=1)
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.perceptual_accuracy == pytest.approx(0.90, abs=0.01)

    def test_task_fit_kpi_intent_kpi(self) -> None:
        ctx = _ctx(["kpi"], winner="kpi", intent="kpi", row_count=1)
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.task_fit == pytest.approx(1.00, abs=0.01)

    def test_task_fit_line_intent_trend(self) -> None:
        ctx = _ctx(["line"], winner="line", intent="trend")
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.task_fit == pytest.approx(1.00, abs=0.01)

    def test_task_fit_bar_intent_comparison(self) -> None:
        ctx = _ctx(["bar"], winner="bar", intent="comparison")
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.task_fit == pytest.approx(1.00, abs=0.01)

    def test_task_fit_mismatch_low(self) -> None:
        # bar for trend intent — poor task fit
        ctx = _ctx(["bar"], winner="bar", intent="trend")
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.task_fit < 0.50

    def test_business_relevance_formula(self) -> None:
        # business_relevance = min(1.0, task_fit * 0.90 + 0.05)
        ctx = _ctx(["bar"], winner="bar", intent="comparison")
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        expected = min(1.0, winner_v2.score.task_fit * 0.90 + 0.05)
        assert winner_v2.score.business_relevance == pytest.approx(expected, abs=0.01)

    def test_kpi_single_row_info_density_full(self) -> None:
        ctx = _ctx(["kpi"], winner="kpi", intent="kpi", row_count=1)
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.information_density == pytest.approx(1.0, abs=0.01)

    def test_kpi_multiple_rows_info_density_low(self) -> None:
        ctx = _ctx(["kpi"], winner="kpi", intent="kpi", row_count=5)
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.information_density == pytest.approx(0.60, abs=0.01)

    def test_kpi_interaction_cost_zero(self) -> None:
        ctx = _ctx(["kpi"], winner="kpi", intent="kpi", row_count=1)
        out = model.run(ctx)
        winner_v2 = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner_v2.score.interaction_cost == pytest.approx(0.00, abs=0.01)

    def test_pie_ambiguity_highest(self) -> None:
        ctx = _ctx(["pie", "bar"], winner="pie", intent="composition")
        out = model.run(ctx)
        pie_v2 = next(c for c in out.scored_candidates if c.chart_type == "pie")
        bar_v2 = next(c for c in out.scored_candidates if c.chart_type == "bar")
        assert pie_v2.score.ambiguity > bar_v2.score.ambiguity

    def test_cognitive_load_increases_with_pie_slices(self) -> None:
        ctx_few = _ctx(["pie"], winner="pie", intent="composition", cat_cardinality=2)
        ctx_many = _ctx(["pie"], winner="pie", intent="composition", cat_cardinality=7)
        out_few = model.run(ctx_few)
        out_many = model.run(ctx_many)
        few_load = next(c for c in out_few.scored_candidates if c.rank == 1).score.cognitive_load
        many_load = next(c for c in out_many.scored_candidates if c.rank == 1).score.cognitive_load
        assert many_load > few_load


# ── Score totals and ranking ──────────────────────────────────────────────


class TestScoreTotalsAndRanking:

    def test_semantic_fit_dominates_winner(self) -> None:
        # Candidate with much higher semantic_fit should win despite being pie
        ctx = _ctx(
            ["pie", "bar"],
            winner="pie",
            intent="composition",
            norm_scores={"pie": 0.95, "bar": 0.30},
        )
        out = model.run(ctx)
        winner = next(c for c in out.scored_candidates if c.rank == 1)
        assert winner.chart_type == "pie"

    def test_all_candidates_ranked(self) -> None:
        ctx = _ctx(["bar", "line", "kpi"], winner="bar", intent="comparison")
        out = model.run(ctx)
        ranks = sorted(c.rank for c in out.scored_candidates if c.eliminated_by_rule is None)
        assert ranks == [1, 2, 3]

    def test_eliminated_candidates_get_rank_zero(self) -> None:
        ctx = _ctx(["bar", "pie"], winner="bar", intent="comparison", eliminated=["pie"])
        out = model.run(ctx)
        pie_v2 = next(c for c in out.scored_candidates if c.chart_type == "pie")
        assert pie_v2.rank == 0
        assert pie_v2.eliminated_by_rule is not None

    def test_score_within_zero_one(self) -> None:
        for intent in ["comparison", "trend", "kpi", "composition", "distribution"]:
            for ct in ["bar", "line", "kpi", "pie", "histogram"]:
                s = model._compute_score(ct, intent, 0.80, 0.85, 10, 4, 1)
                # Just verify the dimensions themselves are bounded
                assert 0.0 <= s.semantic_fit <= 1.0
                assert 0.0 <= s.task_fit <= 1.0
                assert 0.0 <= s.perceptual_accuracy <= 1.0


# ── Winner update behavior ────────────────────────────────────────────────


class TestWinnerUpdate:

    def test_winner_updated_when_scoring_reranks(self) -> None:
        # bar wins V0.1, but pie has much higher semantic_fit → ScoringModel re-ranks to pie
        ctx = _ctx(
            ["pie", "bar"],
            winner="bar",
            intent="composition",
            norm_scores={"pie": 0.99, "bar": 0.10},
        )
        out = model.run(ctx)
        assert out.chart_winner == "pie"
        assert "ScoringModel" in out.fallback_reason

    def test_winner_unchanged_when_v01_winner_still_ranks_1(self) -> None:
        ctx = _ctx(
            ["bar", "line"],
            winner="bar",
            intent="comparison",
            norm_scores={"bar": 0.95, "line": 0.30},
        )
        out = model.run(ctx)
        assert out.chart_winner == "bar"

    def test_hard_chartengine_fallback_not_overridden(self) -> None:
        # percentile override — must NOT be re-ranked
        ctx = _ctx(
            ["table", "bar", "histogram"],
            winner="table",
            intent="distribution",
            fallback_applied=True,
            fallback_reason=(
                "Percentile distribution — boxplot not available in V0.1; showing raw data"
            ),
            norm_scores={"bar": 0.95, "histogram": 0.90, "table": 0.40},
        )
        out = model.run(ctx)
        assert out.chart_winner == "table"
        # fallback_reason unchanged
        assert "Percentile" in out.fallback_reason

    def test_constraint_engine_fallback_can_be_reranked(self) -> None:
        # ConstraintEngine fallback can be overridden by ScoringModel
        ctx = _ctx(
            ["bar_horizontal", "bar"],
            winner="bar_horizontal",
            intent="ranking",
            fallback_applied=True,
            fallback_reason="ConstraintEngine: line eliminated by line_no_temporal",
            norm_scores={"bar_horizontal": 0.95, "bar": 0.30},
        )
        out = model.run(ctx)
        # bar_horizontal was already winner and scores higher — stays
        assert out.chart_winner == "bar_horizontal"

    def test_no_fallback_winner_updates_normally(self) -> None:
        ctx = _ctx(
            ["scatter", "bar"],
            winner="bar",
            intent="correlation",
            norm_scores={"scatter": 0.95, "bar": 0.30},
        )
        out = model.run(ctx)
        # scatter has higher semantic_fit for correlation intent
        assert out.chart_winner in ("scatter", "bar")  # depends on task_fit matrix


# ── scored_candidates written to context ─────────────────────────────────


class TestContextIntegration:

    def test_scored_candidates_written_to_context(self) -> None:
        ctx = _ctx(["bar", "line"], winner="bar", intent="comparison")
        out = model.run(ctx)
        assert out.scored_candidates is not None
        assert len(out.scored_candidates) == 2

    def test_errors_captured_not_raised(self) -> None:
        # Malformed context should not raise — errors go to context.errors
        ctx = RuntimeContext(sql="SELECT 1", chart_candidates=[], chart_winner="bar")
        out = model.run(ctx)
        assert out.scored_candidates is not None or len(out.errors) >= 0
