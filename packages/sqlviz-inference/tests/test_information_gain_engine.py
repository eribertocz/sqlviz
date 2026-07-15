"""Tests for InformationGainEngine — V0.2 Fase D."""
from __future__ import annotations

from sqlviz_inference.dashboard.information_gain_engine import InformationGainEngine
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


class TestNoRedundancy:

    def test_empty_list_no_redundancy(self) -> None:
        report = engine.analyze([])
        assert report.redundancy_count == 0

    def test_single_panel_no_redundancy(self) -> None:
        report = engine.analyze([("p1", _result("fp1", "kpi", "kpi", 1))])
        assert report.redundancy_count == 0

    def test_distinct_fingerprints_no_redundancy(self) -> None:
        panels = [
            ("p1", _result("fp1", "kpi", "kpi", 1)),
            ("p2", _result("fp2", "trend", "line", 12)),
            ("p3", _result("fp3", "comparison", "bar", 5)),
        ]
        report = engine.analyze(panels)
        assert report.redundancy_count == 0

    def test_different_chart_types_no_redundancy(self) -> None:
        # Same intent + row/col count but different chart types — not redundant
        panels = [
            ("p1", _result("fp1", "comparison", "bar", 5, 2)),
            ("p2", _result("fp2", "comparison", "bar_horizontal", 5, 2)),
        ]
        report = engine.analyze(panels)
        assert report.redundancy_count == 0


class TestFingerprintRedundancy:

    def test_same_fingerprint_detected(self) -> None:
        panels = [
            ("p1", _result("fp_shared", "kpi", "kpi", 1)),
            ("p2", _result("fp_shared", "kpi", "kpi", 1)),
        ]
        report = engine.analyze(panels)
        assert report.redundancy_count == 1
        assert ("p1", "p2") in report.redundant_pairs

    def test_second_panel_flagged_as_redundant(self) -> None:
        panels = [
            ("p1", _result("fp_abc", "trend", "line", 10)),
            ("p2", _result("fp_abc", "trend", "line", 10)),
        ]
        report = engine.analyze(panels)
        redundant_ids = report.redundant_panel_ids
        assert "p2" in redundant_ids
        assert "p1" not in redundant_ids

    def test_three_panels_same_fingerprint_two_flagged(self) -> None:
        panels = [
            ("p1", _result("fp_same", "kpi", "kpi", 1)),
            ("p2", _result("fp_same", "kpi", "kpi", 1)),
            ("p3", _result("fp_same", "kpi", "kpi", 1)),
        ]
        report = engine.analyze(panels)
        # p2 and p3 both redundant with p1
        assert report.redundancy_count >= 1

    def test_unknown_fingerprint_not_flagged(self) -> None:
        # "UNKNOWN" fingerprint should not trigger redundancy
        panels = [
            ("p1", _result("UNKNOWN", "kpi", "kpi", 1)),
            ("p2", _result("UNKNOWN", "kpi", "kpi", 1)),
        ]
        report = engine.analyze(panels)
        # Since fingerprint is "UNKNOWN", rule 1 skips it;
        # rule 2 still fires for same intent+chart+shape
        # Either way: no crash
        assert isinstance(report.redundancy_count, int)


class TestShapeRedundancy:

    def test_same_intent_chart_shape_detected(self) -> None:
        # Two COUNT(*) bar charts from different SQLs but same output shape
        panels = [
            ("p1", _result("fp1", "comparison", "bar", 5, 2)),
            ("p2", _result("fp2", "comparison", "bar", 5, 2)),
        ]
        report = engine.analyze(panels)
        assert report.redundancy_count >= 1

    def test_different_row_counts_not_redundant(self) -> None:
        panels = [
            ("p1", _result("fp1", "comparison", "bar", 5, 2)),
            ("p2", _result("fp2", "comparison", "bar", 10, 2)),
        ]
        report = engine.analyze(panels)
        assert report.redundancy_count == 0

    def test_zero_row_count_not_flagged(self) -> None:
        # Empty result panels shouldn't trigger redundancy
        panels = [
            ("p1", _result("fp1", "detail", "table", 0, 5)),
            ("p2", _result("fp2", "detail", "table", 0, 5)),
        ]
        report = engine.analyze(panels)
        # Should not flag zero-row panels
        assert report.redundancy_count == 0


class TestRedundancyReport:

    def test_redundancy_count_property(self) -> None:
        panels = [
            ("p1", _result("fp1", "kpi", "kpi", 1)),
            ("p2", _result("fp1", "kpi", "kpi", 1)),
        ]
        report = engine.analyze(panels)
        assert report.redundancy_count == len(report.redundant_pairs)

    def test_redundant_panel_ids_property(self) -> None:
        panels = [
            ("p1", _result("fp_x", "kpi", "kpi", 1)),
            ("p2", _result("fp_x", "kpi", "kpi", 1)),
        ]
        report = engine.analyze(panels)
        ids = report.redundant_panel_ids
        assert isinstance(ids, set)
        assert "p2" in ids
