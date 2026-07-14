"""Scoring annotation verification — DOC10 Fase C.

For each gold case annotated in scoring_annotations.yaml, verify that the
winner's dominant scoring dimension (by weighted contribution) matches
top_dimensions[0], and that all three annotated dimensions appear in the
actual top-5 highest-contributing dimensions.

This goes beyond "did the right chart win?" to "did it win for the right reasons?"
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.contracts.chart import ChartScore
from sqlviz_inference.pipeline import RuntimePipeline

_ANNOTATIONS_PATH = Path(__file__).parent / "benchmark" / "scoring_annotations.yaml"
_CASES_PATH = Path(__file__).parent / "benchmark" / "benchmark_cases.yaml"

_WEIGHTS_POS = {
    "semantic_fit": 0.45,
    "task_fit": 0.20,
    "perceptual_accuracy": 0.10,
    "readability": 0.08,
    "information_density": 0.06,
    "business_relevance": 0.06,
}
_WEIGHTS_NEG = {
    "cognitive_load": 0.02,
    "visual_clutter": 0.01,
    "ambiguity": 0.01,
    "interaction_cost": 0.01,
}


def _weighted_contributions(score: ChartScore) -> dict[str, float]:
    return {
        "semantic_fit": _WEIGHTS_POS["semantic_fit"] * score.semantic_fit,
        "task_fit": _WEIGHTS_POS["task_fit"] * score.task_fit,
        "perceptual_accuracy": _WEIGHTS_POS["perceptual_accuracy"] * score.perceptual_accuracy,
        "readability": _WEIGHTS_POS["readability"] * score.readability,
        "information_density": _WEIGHTS_POS["information_density"] * score.information_density,
        "business_relevance": _WEIGHTS_POS["business_relevance"] * score.business_relevance,
        # Negative dims: lower value = smaller negative contribution = "better"
        "cognitive_load": _WEIGHTS_NEG["cognitive_load"] * (1.0 - score.cognitive_load),
        "visual_clutter": _WEIGHTS_NEG["visual_clutter"] * (1.0 - score.visual_clutter),
        "ambiguity": _WEIGHTS_NEG["ambiguity"] * (1.0 - score.ambiguity),
        "interaction_cost": _WEIGHTS_NEG["interaction_cost"] * (1.0 - score.interaction_cost),
    }


def _top_dims(score: ChartScore, n: int = 5) -> list[str]:
    contribs = _weighted_contributions(score)
    return sorted(contribs, key=lambda k: contribs[k], reverse=True)[:n]


def load_annotations() -> dict[str, dict]:
    with open(_ANNOTATIONS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {c["id"]: c for c in data["cases"]}


def load_gold_cases() -> list[dict]:
    with open(_CASES_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]


_pipeline = RuntimePipeline()
_annotations = load_annotations()
_gold_cases = load_gold_cases()


def _run_case(case: dict) -> RuntimeContext:
    schema = [ColumnSchema(name=c["name"], type=c["type"]) for c in case.get("schema", [])]
    ctx = RuntimeContext(sql=case["sql"], data=case.get("data") or [], schema=schema)
    return _pipeline.run(ctx)


def pytest_generate_tests(metafunc):
    if "gold_case_and_annotation" in metafunc.fixturenames:
        params = [
            (case, _annotations[case["id"]])
            for case in _gold_cases
            if case["id"] in _annotations
        ]
        metafunc.parametrize(
            "gold_case_and_annotation",
            params,
            ids=[case["id"] for case, _ in params],
        )


class TestScoringAnnotations:

    def test_winner_chart_matches_annotation(self, gold_case_and_annotation) -> None:
        case, annotation = gold_case_and_annotation
        ctx = _run_case(case)
        assert ctx.chart_winner == annotation["expected_chart"], (
            f"[{case['id']}] expected chart={annotation['expected_chart']} "
            f"got {ctx.chart_winner}"
        )

    def test_top_dimension_matches_annotation(self, gold_case_and_annotation) -> None:
        case, annotation = gold_case_and_annotation
        ctx = _run_case(case)

        if not ctx.scored_candidates:
            pytest.skip(f"[{case['id']}] no scored_candidates")

        winner_v2 = next(
            (c for c in ctx.scored_candidates if c.chart_type == ctx.chart_winner and c.rank == 1),
            None,
        )
        if winner_v2 is None:
            # Winner may not have rank=1 if scoring model couldn't update (hard fallback)
            winner_v2 = next(
                (c for c in ctx.scored_candidates if c.chart_type == ctx.chart_winner),
                None,
            )
        if winner_v2 is None:
            pytest.skip(f"[{case['id']}] winner {ctx.chart_winner} not in scored_candidates")

        expected_top_dim = annotation["top_dimensions"][0]
        actual_top_dims = _top_dims(winner_v2.score, n=5)

        assert expected_top_dim == actual_top_dims[0], (
            f"[{case['id']}] expected top dimension={expected_top_dim} "
            f"got top-5={actual_top_dims}. "
            f"Score: {winner_v2.score}"
        )

    def test_annotated_dimensions_in_top5(self, gold_case_and_annotation) -> None:
        case, annotation = gold_case_and_annotation
        ctx = _run_case(case)

        if not ctx.scored_candidates:
            pytest.skip(f"[{case['id']}] no scored_candidates")

        winner_v2 = next(
            (c for c in ctx.scored_candidates if c.chart_type == ctx.chart_winner),
            None,
        )
        if winner_v2 is None:
            pytest.skip(f"[{case['id']}] winner {ctx.chart_winner} not in scored_candidates")

        actual_top5 = set(_top_dims(winner_v2.score, n=5))
        annotated = annotation["top_dimensions"]

        missing = [d for d in annotated if d not in actual_top5]
        assert not missing, (
            f"[{case['id']}] annotated dimensions {missing} not found in top-5 "
            f"actual={list(actual_top5)}. Score: {winner_v2.score}"
        )
