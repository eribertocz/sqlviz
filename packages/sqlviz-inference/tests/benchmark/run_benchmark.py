"""Benchmark runner — DOC5 Section 14.4."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.pipeline import RuntimePipeline


def load_benchmark_cases() -> list[dict[str, Any]]:
    path = Path(__file__).parent / "benchmark_cases.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]  # type: ignore[no-any-return]


def run_benchmark() -> dict[str, Any]:
    """
    Run all benchmark cases and compute accuracy metrics.

    Returns:
        {
            "total_cases": int,
            "intent_accuracy": float,
            "chart_accuracy": float,
            "quality_pass_rate": float,
            "failures": list[dict]
        }
    """
    cases = load_benchmark_cases()
    pipeline = RuntimePipeline()

    intent_correct = 0
    chart_correct = 0
    quality_pass = 0
    failures: list[dict[str, Any]] = []

    quality_rank: dict[str, int] = {"high": 3, "medium": 2, "low": 1}

    for case in cases:
        schema = [
            ColumnSchema(name=c["name"], type=c["type"])
            for c in case.get("schema", [])
        ]
        ctx = RuntimeContext(
            sql=case["sql"],
            data=case.get("data") or [],
            schema=schema,
        )
        ctx = pipeline.run(ctx)

        intent_match = ctx.intent_winner == case["expected_intent"]
        chart_match = ctx.chart_winner == case["expected_chart"]
        min_quality = case.get("min_quality", "low")
        quality_ok = (
            quality_rank.get(ctx.chart_quality, 0)
            >= quality_rank.get(min_quality, 0)
        )

        if intent_match:
            intent_correct += 1
        if chart_match:
            chart_correct += 1
        if quality_ok:
            quality_pass += 1

        if not (intent_match and chart_match and quality_ok):
            failures.append(
                {
                    "id": case["id"],
                    "sql": case["sql"],
                    "expected_intent": case["expected_intent"],
                    "actual_intent": ctx.intent_winner,
                    "expected_chart": case["expected_chart"],
                    "actual_chart": ctx.chart_winner,
                    "expected_min_quality": min_quality,
                    "actual_quality": ctx.chart_quality,
                    "notes": case.get("notes", ""),
                }
            )

    total = len(cases)
    return {
        "total_cases": total,
        "intent_accuracy": round(intent_correct / total, 4),
        "chart_accuracy": round(chart_correct / total, 4),
        "quality_pass_rate": round(quality_pass / total, 4),
        "failures": failures,
    }


if __name__ == "__main__":
    results = run_benchmark()
    sep = "=" * 60
    print(f"\n{sep}")
    print("SQLviz Inference Engine — Benchmark Results")
    print(sep)
    print(f"Total cases:       {results['total_cases']}")
    print(f"Intent accuracy:   {results['intent_accuracy'] * 100:.1f}%")
    print(f"Chart accuracy:    {results['chart_accuracy'] * 100:.1f}%")
    print(f"Quality pass rate: {results['quality_pass_rate'] * 100:.1f}%")

    if results["failures"]:
        print(f"\n{len(results['failures'])} FAILURES:\n")
        for f in results["failures"]:
            print(f"  [{f['id']}] {f['notes']}")
            print(
                f"    Intent: expected={f['expected_intent']}"
                f" actual={f['actual_intent']}"
            )
            print(
                f"    Chart:  expected={f['expected_chart']}"
                f" actual={f['actual_chart']}"
            )
            print(
                f"    Quality: expected>={f['expected_min_quality']}"
                f" actual={f['actual_quality']}"
            )
            print()
    else:
        print("\nAll cases passed!")
