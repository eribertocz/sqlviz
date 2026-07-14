"""Tests for ExplanationEngine V2 (DOC10 §6.16) — Fase F."""
from __future__ import annotations

from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.contracts.chart import ChartCandidate, ChartScore
from sqlviz_inference.contracts.constraint import ConstraintReport, ConstraintViolation
from sqlviz_inference.explanation.explanation_engine import ExplanationEngine

engine = ExplanationEngine()


def _ctx(
    intent: str = "trend",
    chart: str = "line",
    scored_candidates: list[ChartCandidate] | None = None,
    constraint_report: ConstraintReport | None = None,
) -> RuntimeContext:
    return RuntimeContext(
        sql="SELECT date, revenue FROM sales",
        intent_winner=intent,
        chart_winner=chart,
        scored_candidates=scored_candidates,
        constraint_report=constraint_report,
    )


def _candidate(chart: str, rank: int, score: float = 0.5) -> ChartCandidate:
    cs = ChartScore(semantic_fit=score)
    return ChartCandidate(chart_type=chart, score=cs, rank=rank)


def _violation(chart: str, reason: str = "hard rule") -> ConstraintViolation:
    return ConstraintViolation(
        chart_type=chart,
        rule_name="test_rule",
        rule_type="hard",
        reason=reason,
    )


# ── Explanation dataclass ──────────────────────────────────────────────────────


def test_explanation_fields_populated() -> None:
    ctx = _ctx("trend", "line")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert exp.chart_winner == "line"
    assert exp.intent == "trend"


def test_explanation_reason_main_non_empty() -> None:
    ctx = _ctx("trend", "line")
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert len(ctx.explanation_v2.reason_main) > 0


def test_explanation_full_text_non_empty() -> None:
    ctx = _ctx("trend", "line")
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert len(ctx.explanation_v2.full_text) > 0


def test_explanation_full_text_starts_with_elegi() -> None:
    ctx = _ctx("trend", "line")
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert ctx.explanation_v2.full_text.startswith("Elegí")


# ── Template lookup ────────────────────────────────────────────────────────────


def test_exact_template_trend_line() -> None:
    ctx = _ctx("trend", "line")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "temporal" in exp.reason_main or "continuo" in exp.reason_main


def test_exact_template_kpi_kpi() -> None:
    ctx = _ctx("kpi", "kpi")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "KPI" in exp.full_text or "métrica" in exp.reason_main


def test_exact_template_comparison_bar() -> None:
    ctx = _ctx("comparison", "bar")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "categor" in exp.reason_main or "barra" in exp.reason_main


def test_exact_template_distribution_histogram() -> None:
    ctx = _ctx("distribution", "histogram")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "distribuc" in exp.reason_main or "continua" in exp.reason_main


def test_exact_template_correlation_scatter() -> None:
    ctx = _ctx("correlation", "scatter")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "correlaci" in exp.reason_main or "variable" in exp.reason_main


def test_exact_template_ranking_bar_horizontal() -> None:
    ctx = _ctx("ranking", "bar_horizontal")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "ranking" in exp.reason_main or "horizontal" in exp.reason_main


def test_exact_template_composition_pie() -> None:
    ctx = _ctx("composition", "pie")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert (
        "partes" in exp.reason_main
        or "todo" in exp.reason_main
        or "proporciones" in exp.reason_main
    )


# ── Fallback when no exact template ───────────────────────────────────────────


def test_fallback_to_intent_fallback_when_no_exact_match() -> None:
    # "trend" + "scatter" has no exact template → uses intent_fallback["trend"]
    ctx = _ctx("trend", "scatter")
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert len(exp.reason_main) > 0
    assert exp.chart_winner == "scatter"


def test_fallback_reason_main_non_empty_for_unknown_combination() -> None:
    ctx = _ctx("detail", "scatter")  # no template for this pair
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert len(ctx.explanation_v2.reason_main) > 0


# ── alternatives_considered ───────────────────────────────────────────────────


def test_alternatives_considered_excludes_winner() -> None:
    candidates = [
        _candidate("line", rank=1),
        _candidate("bar", rank=2),
        _candidate("table", rank=3),
    ]
    ctx = _ctx("trend", "line", scored_candidates=candidates)
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert "line" not in exp.alternatives_considered


def test_alternatives_considered_max_two() -> None:
    candidates = [
        _candidate("line", rank=1),
        _candidate("bar", rank=2),
        _candidate("table", rank=3),
        _candidate("pie", rank=4),
    ]
    ctx = _ctx("trend", "line", scored_candidates=candidates)
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert len(ctx.explanation_v2.alternatives_considered) <= 2


def test_alternatives_considered_sorted_by_rank() -> None:
    candidates = [
        _candidate("line", rank=1),
        _candidate("table", rank=3),
        _candidate("bar", rank=2),
    ]
    ctx = _ctx("trend", "line", scored_candidates=candidates)
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    assert exp.alternatives_considered == ["bar", "table"]


def test_alternatives_considered_empty_when_no_candidates() -> None:
    ctx = _ctx("trend", "line", scored_candidates=[])
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert ctx.explanation_v2.alternatives_considered == []


def test_alternatives_considered_excludes_rank_zero() -> None:
    candidates = [
        _candidate("line", rank=1),
        _candidate("bar", rank=0),   # rank=0 means not ranked (eliminated before scoring)
    ]
    ctx = _ctx("trend", "line", scored_candidates=candidates)
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert "bar" not in ctx.explanation_v2.alternatives_considered


# ── alternatives_rejected ─────────────────────────────────────────────────────


def test_alternatives_rejected_from_constraint_report() -> None:
    violations = [_violation("pie", "no puede mostrar series temporales")]
    report = ConstraintReport(eliminated=violations)
    ctx = _ctx("trend", "line", constraint_report=report)
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    rejected_charts = [r["chart"] for r in exp.alternatives_rejected]
    assert "pie" in rejected_charts


def test_alternatives_rejected_excludes_winner() -> None:
    violations = [_violation("line", "winner should not appear")]
    report = ConstraintReport(eliminated=violations)
    ctx = _ctx("trend", "line", constraint_report=report)
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    rejected_charts = [r["chart"] for r in exp.alternatives_rejected]
    assert "line" not in rejected_charts


def test_alternatives_rejected_empty_when_no_constraint_report() -> None:
    ctx = _ctx("trend", "line", constraint_report=None)
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert ctx.explanation_v2.alternatives_rejected == []


def test_alternatives_rejected_uses_template_reason_over_violation_reason() -> None:
    # trend_line template has reject_pie key — should use it over violation reason
    violations = [_violation("pie", "generic hard rule reason")]
    report = ConstraintReport(eliminated=violations)
    ctx = _ctx("trend", "line", constraint_report=report)
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    pie_entries = [r for r in exp.alternatives_rejected if r["chart"] == "pie"]
    assert len(pie_entries) == 1
    assert pie_entries[0]["reason"] != "generic hard rule reason"


def test_alternatives_rejected_no_duplicates() -> None:
    violations = [
        _violation("pie", "reason 1"),
        _violation("pie", "reason 2"),
    ]
    report = ConstraintReport(eliminated=violations)
    ctx = _ctx("trend", "line", constraint_report=report)
    ctx = engine.run(ctx)
    exp = ctx.explanation_v2
    assert exp is not None
    pie_entries = [r for r in exp.alternatives_rejected if r["chart"] == "pie"]
    assert len(pie_entries) == 1


# ── full_text assembly ─────────────────────────────────────────────────────────


def test_full_text_mentions_rejected_alternative() -> None:
    violations = [_violation("pie", "no puede mostrar series temporales")]
    report = ConstraintReport(eliminated=violations)
    ctx = _ctx("trend", "line", constraint_report=report)
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert "circular" in ctx.explanation_v2.full_text or "pie" in ctx.explanation_v2.full_text


def test_full_text_mentions_considered_alternative() -> None:
    candidates = [
        _candidate("line", rank=1),
        _candidate("bar", rank=2),
    ]
    ctx = _ctx("trend", "line", scored_candidates=candidates)
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None
    assert "barras" in ctx.explanation_v2.full_text or "bar" in ctx.explanation_v2.full_text


# ── Graceful degradation ───────────────────────────────────────────────────────


def test_run_does_not_raise_on_empty_context() -> None:
    ctx = RuntimeContext(sql="SELECT 1")
    ctx = engine.run(ctx)
    assert ctx.explanation_v2 is not None


def test_run_appends_error_on_exception_and_returns_fallback() -> None:
    # Monkeypatch _build to simulate an error
    original = engine._build
    engine._build = lambda ctx: (_ for _ in ()).throw(RuntimeError("test error"))  # type: ignore[assignment]
    try:
        ctx = RuntimeContext(sql="SELECT 1")
        ctx = engine.run(ctx)
        assert ctx.explanation_v2 is not None
        assert any("ExplanationEngine" in e for e in ctx.errors)
    finally:
        engine._build = original  # type: ignore[assignment]
