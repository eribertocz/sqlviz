"""Golden serialization tests for versioned contracts.

These tests freeze the JSON output shape of InferenceResult and VisualSpec.
They fail when any field is added, removed, or renamed — a deliberate signal
that a contract change happened and the golden fixture must be updated.

To update the fixture after an intentional (backward-compatible) change:
    1. Run the test to see which fields differ.
    2. Update the relevant golden/*.json file.
    3. Commit fixture + code change together.

For breaking changes (field removed or renamed): bump schema_version in
result.py or visual_spec.py before updating the fixture.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import cast

from sqlviz_inference.result import INFERENCE_RESULT_SCHEMA_VERSION, InferenceResult
from sqlviz_inference.spec.visual_spec import VISUAL_SPEC_SCHEMA_VERSION, VisualSpec

GOLDEN_DIR = Path(__file__).parent / "golden"


def _load_golden(filename: str) -> list[str]:
    return cast(list[str], json.loads((GOLDEN_DIR / filename).read_text(encoding="utf-8")))


def _minimal_inference_result() -> InferenceResult:
    return InferenceResult(
        rules_version="v0.1.0",
        feature_vector_version="v0",
        engine_version="sqlviz-inference-0.1.0",
        intent_winner="comparison",
        intent_raw_score=0.8,
        intent_normalized_score=0.9,
        intent_confidence_gap=0.3,
        intent_quality="high",
        intent_alternatives=[],
        chart_winner="bar",
        chart_raw_score=0.75,
        chart_normalized_score=0.85,
        chart_confidence_gap=0.2,
        chart_quality="high",
        chart_alternatives=[],
        col_span=6,
        row_span=1,
        layout_importance=0.5,
        panel_height_px=360,
        trend_direction_label="unknown",
        filter_controls=[],
        title="Revenue by Category",
        title_confidence=0.9,
        fallback_applied=False,
        fallback_reason="",
        explanation=[],
        score_trace={},
        fingerprint="abc123",
        feature_vector=[0.0] * 39,
        errors=[],
        elapsed_ms=15.0,
    )


class TestVisualSpecGolden:
    def test_field_set_unchanged(self) -> None:
        spec = VisualSpec(
            chart_type="bar",
            x_field="category",
            y_fields=["revenue"],
            orientation="vertical",
            sort_order="desc",
            color_field=None,
            stack=False,
            number_format="default",
        )
        actual_keys = sorted(asdict(spec).keys())
        expected_keys = _load_golden("visual_spec_fields.json")

        added = sorted(set(actual_keys) - set(expected_keys))
        removed = sorted(set(expected_keys) - set(actual_keys))

        assert not added and not removed, (
            "VisualSpec shape changed — update golden/visual_spec_fields.json "
            "and bump VISUAL_SPEC_SCHEMA_VERSION if the change is breaking.\n"
            f"  Added:   {added}\n"
            f"  Removed: {removed}"
        )

    def test_schema_version_present(self) -> None:
        spec = VisualSpec(
            chart_type="kpi",
            x_field=None,
            y_fields=["total"],
            orientation="none",
            sort_order="none",
            color_field=None,
            stack=False,
            number_format="default",
        )
        assert spec.schema_version == VISUAL_SPEC_SCHEMA_VERSION
        assert spec.schema_version != ""


class TestInferenceResultGolden:
    def test_field_set_unchanged(self) -> None:
        result = _minimal_inference_result()
        actual_keys = sorted(asdict(result).keys())
        expected_keys = _load_golden("inference_result_fields.json")

        added = sorted(set(actual_keys) - set(expected_keys))
        removed = sorted(set(expected_keys) - set(actual_keys))

        assert not added and not removed, (
            "InferenceResult shape changed — update golden/inference_result_fields.json "
            "and bump INFERENCE_RESULT_SCHEMA_VERSION if the change is breaking.\n"
            f"  Added:   {added}\n"
            f"  Removed: {removed}"
        )

    def test_schema_version_present(self) -> None:
        result = _minimal_inference_result()
        assert result.result_schema_version == INFERENCE_RESULT_SCHEMA_VERSION
        assert result.result_schema_version != ""

    def test_to_dict_includes_schema_version(self) -> None:
        result = _minimal_inference_result()
        d = result.to_dict()
        assert "result_schema_version" in d
        assert d["result_schema_version"] == INFERENCE_RESULT_SCHEMA_VERSION
