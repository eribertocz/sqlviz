"""Tests for InformationGainEngine V2 — recommendations (DOC10 Fase F)."""
from __future__ import annotations

from sqlviz_inference.dashboard.information_gain_engine import (
    InformationGainEngine,
    RedundancyReport,
)
from sqlviz_inference.profile.data_profile import DataProfile
from sqlviz_inference.result import InferenceResult


def _result(
    fingerprint: str,
    intent: str,
    chart: str,
    row_count: int = 10,
    col_count: int = 2,
) -> InferenceResult:
    dp = DataProfile(
        row_count=row_count,
        col_count=col_count,
        single_row=(row_count == 1),
        wide_table=False,
    )
    return InferenceResult(
        rules_version="v0.1.0",
        feature_vector_version="v0",
        engine_version="test",
        intent_winner=intent,
        intent_raw_score=0.9,
        intent_normalized_score=0.9,
        intent_confidence_gap=0.1,
        intent_quality="high",
        intent_alternatives=[],
        chart_winner=chart,
        chart_raw_score=0.9,
        chart_normalized_score=0.9,
        chart_confidence_gap=0.1,
        chart_quality="high",
        chart_alternatives=[],
        col_span=12,
        row_span=2,
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
        fingerprint=fingerprint,
        feature_vector=[0.0] * 39,
        errors=[],
        elapsed_ms=10.0,
        data_profile=dp,
    )


engine = InformationGainEngine()


# ── RedundancyReport.recommendations field ────────────────────────────────────


def test_report_recommendations_empty_by_default() -> None:
    report = RedundancyReport()
    assert report.recommendations == {}


def test_report_recommendation_for_returns_none_when_absent() -> None:
    report = RedundancyReport()
    assert report.recommendation_for("panel_x") is None


def test_report_recommendation_for_returns_value_when_present() -> None:
    report = RedundancyReport(recommendations={"p1": "remove"})
    assert report.recommendation_for("p1") == "remove"


# ── Rule 1 (fingerprint match) → "remove" ────────────────────────────────────


def test_fingerprint_match_recommends_remove() -> None:
    panels = [
        ("p1", _result("fp_abc", "comparison", "bar")),
        ("p2", _result("fp_abc", "comparison", "bar")),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p2") == "remove"


def test_fingerprint_match_does_not_recommend_first_panel() -> None:
    panels = [
        ("p1", _result("fp_abc", "comparison", "bar")),
        ("p2", _result("fp_abc", "comparison", "bar")),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p1") is None


def test_fingerprint_match_third_duplicate_also_remove() -> None:
    panels = [
        ("p1", _result("fp_abc", "comparison", "bar")),
        ("p2", _result("fp_abc", "comparison", "bar")),
        ("p3", _result("fp_abc", "comparison", "bar")),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p2") == "remove"
    assert report.recommendation_for("p3") == "remove"


def test_unknown_fingerprint_does_not_trigger_rule1() -> None:
    panels = [
        ("p1", _result("UNKNOWN", "comparison", "bar")),
        ("p2", _result("UNKNOWN", "comparison", "bar", row_count=99)),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p1") is None
    assert report.recommendation_for("p2") is None


# ── Rule 2 (shape match, non-table) → "convert_to_table" ─────────────────────


def test_shape_match_non_table_recommends_convert_to_table() -> None:
    panels = [
        ("p1", _result("fp_a", "comparison", "bar", row_count=10, col_count=2)),
        ("p2", _result("fp_b", "comparison", "bar", row_count=10, col_count=2)),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p2") == "convert_to_table"


def test_shape_match_non_table_does_not_flag_first_panel() -> None:
    panels = [
        ("p1", _result("fp_a", "comparison", "bar", row_count=10, col_count=2)),
        ("p2", _result("fp_b", "comparison", "bar", row_count=10, col_count=2)),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p1") is None


# ── Rule 2 (shape match, chart == "table") → "lower_priority" ─────────────────


def test_shape_match_table_chart_recommends_lower_priority() -> None:
    panels = [
        ("p1", _result("fp_a", "detail", "table", row_count=5, col_count=4)),
        ("p2", _result("fp_b", "detail", "table", row_count=5, col_count=4)),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p2") == "lower_priority"


# ── Rule priority: fingerprint match skips rule 2 ─────────────────────────────


def test_fingerprint_rule_takes_priority_over_shape_rule() -> None:
    panels = [
        ("p1", _result("fp_same", "comparison", "bar", row_count=10, col_count=2)),
        ("p2", _result("fp_same", "comparison", "bar", row_count=10, col_count=2)),
    ]
    report = engine.analyze(panels)
    assert report.recommendation_for("p2") == "remove"


# ── No redundancy ─────────────────────────────────────────────────────────────


def test_distinct_fingerprints_distinct_shapes_no_recommendations() -> None:
    panels = [
        ("p1", _result("fp_a", "trend", "line", row_count=20, col_count=2)),
        ("p2", _result("fp_b", "comparison", "bar", row_count=5, col_count=2)),
        ("p3", _result("fp_c", "kpi", "kpi", row_count=1, col_count=1)),
    ]
    report = engine.analyze(panels)
    assert report.recommendations == {}


def test_single_panel_no_recommendations() -> None:
    panels = [("p1", _result("fp_a", "trend", "line"))]
    report = engine.analyze(panels)
    assert report.recommendations == {}


def test_empty_panels_no_recommendations() -> None:
    report = engine.analyze([])
    assert report.recommendations == {}


# ── recommendation_for consistency with redundant_pairs ──────────────────────


def test_recommendations_keys_subset_of_redundant_panel_ids() -> None:
    panels = [
        ("p1", _result("fp_abc", "comparison", "bar")),
        ("p2", _result("fp_abc", "comparison", "bar")),
        ("p3", _result("fp_xyz", "trend", "line")),
    ]
    report = engine.analyze(panels)
    redundant_ids = report.redundant_panel_ids
    for panel_id in report.recommendations:
        assert panel_id in redundant_ids


def test_all_recommendation_values_are_valid_actions() -> None:
    valid = {"remove", "lower_priority", "convert_to_table"}
    panels = [
        ("p1", _result("fp_abc", "comparison", "bar", row_count=8, col_count=2)),
        ("p2", _result("fp_abc", "comparison", "bar", row_count=8, col_count=2)),
        ("p3", _result("fp_xyz", "detail", "table", row_count=8, col_count=2)),
        ("p4", _result("fp_def", "detail", "table", row_count=8, col_count=2)),
    ]
    report = engine.analyze(panels)
    for action in report.recommendations.values():
        assert action in valid
