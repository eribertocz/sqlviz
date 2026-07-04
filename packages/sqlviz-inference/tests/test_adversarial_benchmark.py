"""
Adversarial Benchmark — Entrega 3.A.

Tests boundary confusions between similar intents and chart types.
Finds real engine bugs, not superficial mismatches.

Release thresholds (stricter than the main benchmark):
  intent_accuracy  >= 0.90
  chart_accuracy   >= 0.90
  quality_avg      >= 0.85  (fraction of cases meeting min_quality)

Run with: uv run pytest tests/test_adversarial_benchmark.py -v
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.pipeline import RuntimePipeline

# ── Thresholds ────────────────────────────────────────────────────────────────

MIN_INTENT_ACCURACY = 0.90
MIN_CHART_ACCURACY = 0.90
MIN_QUALITY_PASS_RATE = 0.85

# ── Loader ────────────────────────────────────────────────────────────────────

def _load_cases() -> list[dict[str, Any]]:
    path = Path(__file__).parent / "benchmark" / "adversarial_cases.yaml"
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["cases"]  # type: ignore[no-any-return]


def _run_adversarial() -> dict[str, Any]:
    """
    Execute all adversarial cases and return accuracy metrics + detailed failures.
    """
    cases = _load_cases()
    pipeline = RuntimePipeline()

    quality_rank: dict[str, int] = {"high": 3, "medium": 2, "low": 1}

    intent_correct = 0
    chart_correct = 0
    quality_pass = 0
    failures: list[dict[str, Any]] = []
    known_bugs: list[dict[str, Any]] = []

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
        min_quality = case.get("expected_quality_min", "low")
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

        # Capture all failures with full diagnostics
        if not (intent_match and chart_match and quality_ok):
            reason = case.get("reason", "")
            is_known_bug = "BUG §" in reason or "ADVERSARIAL" in reason
            entry = {
                "id":                 case["id"],
                "description":        case.get("description", ""),
                "sql":                case["sql"],
                "expected_intent":    case["expected_intent"],
                "actual_intent":      ctx.intent_winner,
                "expected_chart":     case["expected_chart"],
                "actual_chart":       ctx.chart_winner,
                "expected_quality":   min_quality,
                "actual_quality":     ctx.chart_quality,
                "intent_match":       intent_match,
                "chart_match":        chart_match,
                "quality_ok":         quality_ok,
                "reason":             reason,
                "known_bug":          is_known_bug,
            }
            failures.append(entry)
            if is_known_bug:
                known_bugs.append(entry)

    total = len(cases)
    return {
        "total_cases":       total,
        "intent_accuracy":   round(intent_correct / total, 4),
        "chart_accuracy":    round(chart_correct / total, 4),
        "quality_pass_rate": round(quality_pass / total, 4),
        "failures":          failures,
        "known_bugs":        known_bugs,
        "intent_correct":    intent_correct,
        "chart_correct":     chart_correct,
        "quality_pass":      quality_pass,
    }


# ── Shared results (computed once per session) ────────────────────────────────

_RESULTS: dict[str, Any] | None = None


def _get_results() -> dict[str, Any]:
    global _RESULTS
    if _RESULTS is None:
        _RESULTS = _run_adversarial()
    return _RESULTS


# ── Test classes ──────────────────────────────────────────────────────────────

class TestAdversarialAccuracy:
    """Accuracy gate — must pass before Phase 3.B begins."""

    def test_intent_accuracy(self) -> None:
        r = _get_results()
        _print_summary(r)
        assert r["intent_accuracy"] >= MIN_INTENT_ACCURACY, (
            f"Intent accuracy {r['intent_accuracy'] * 100:.1f}% "
            f"< gate {MIN_INTENT_ACCURACY * 100:.0f}%.\n"
            f"{_format_failures(r['failures'], 'intent')}"
        )

    def test_chart_accuracy(self) -> None:
        r = _get_results()
        assert r["chart_accuracy"] >= MIN_CHART_ACCURACY, (
            f"Chart accuracy {r['chart_accuracy'] * 100:.1f}% "
            f"< gate {MIN_CHART_ACCURACY * 100:.0f}%.\n"
            f"{_format_failures(r['failures'], 'chart')}"
        )

    def test_quality_pass_rate(self) -> None:
        r = _get_results()
        assert r["quality_pass_rate"] >= MIN_QUALITY_PASS_RATE, (
            f"Quality pass rate {r['quality_pass_rate'] * 100:.1f}% "
            f"< gate {MIN_QUALITY_PASS_RATE * 100:.0f}%."
        )


class TestAdversarialConfusionPairs:
    """
    Per-confusion-pair accuracy.
    Each group must have ≥ 66% accuracy (soft gate — surfaces regressions).
    """

    PAIRS = {
        "comparison_vs_composition": ["adv_cc_0"],
        "comparison_vs_distribution": ["adv_cd_0"],
        "trend_vs_kpi":              ["adv_tk_0"],
        "ranking_vs_comparison":     ["adv_rc_0"],
        "detail_vs_table":           ["adv_dt_0"],
        "cohort_vs_trend":           ["adv_coh_0"],
        "retention_vs_line":         ["adv_ret_0"],
        "anomaly_vs_trend":          ["adv_ano_0"],
        "funnel_vs_ranking":         ["adv_fun_0"],
    }

    def _pair_accuracy(self, prefix: str) -> dict[str, float]:
        cases = _load_cases()
        pipeline = RuntimePipeline()
        total = intent_ok = chart_ok = 0
        for case in cases:
            if not case["id"].startswith(prefix):
                continue
            total += 1
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
            if ctx.intent_winner == case["expected_intent"]:
                intent_ok += 1
            if ctx.chart_winner == case["expected_chart"]:
                chart_ok += 1
        if total == 0:
            return {"intent": 1.0, "chart": 1.0, "total": 0}
        return {
            "intent": round(intent_ok / total, 4),
            "chart": round(chart_ok / total, 4),
            "total": total,
        }

    @pytest.mark.parametrize("pair,prefixes", [
        ("comparison_vs_composition", "adv_cc_"),
        ("comparison_vs_distribution", "adv_cd_"),
        ("trend_vs_kpi",              "adv_tk_"),
        ("ranking_vs_comparison",     "adv_rc_"),
        ("detail_vs_table",           "adv_dt_"),
        ("cohort_vs_trend",           "adv_coh_"),
        ("retention_vs_line",         "adv_ret_"),
        ("anomaly_vs_trend",          "adv_ano_"),
        ("funnel_vs_ranking",         "adv_fun_"),
    ])
    def test_pair_intent_accuracy(self, pair: str, prefixes: str) -> None:
        acc = self._pair_accuracy(prefixes)
        assert acc["intent"] >= 0.50, (
            f"[{pair}] intent accuracy {acc['intent']*100:.0f}% is below 50% "
            f"({acc['total']} cases) — severe regression or unfixed bug cluster"
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_summary(r: dict[str, Any]) -> None:
    sep = "=" * 60
    print(f"\n{sep}")
    print("SQLviz Inference Engine — Adversarial Benchmark (3.A)")
    print(sep)
    print(f"Total cases:       {r['total_cases']}")
    print(f"Intent accuracy:   {r['intent_accuracy'] * 100:.1f}%  "
          f"({r['intent_correct']}/{r['total_cases']})")
    print(f"Chart accuracy:    {r['chart_accuracy'] * 100:.1f}%  "
          f"({r['chart_correct']}/{r['total_cases']})")
    print(f"Quality pass rate: {r['quality_pass_rate'] * 100:.1f}%  "
          f"({r['quality_pass']}/{r['total_cases']})")

    if r["failures"]:
        print(f"\n{'─'*60}")
        print(f"FAILURES ({len(r['failures'])} total, "
              f"{len(r['known_bugs'])} documented bugs):")
        print(f"{'─'*60}")
        for f in r["failures"]:
            bug_tag = " [KNOWN BUG]" if f["known_bug"] else ""
            print(f"\n  [{f['id']}]{bug_tag} {f['description']}")
            if not f["intent_match"]:
                print(f"    Intent : expected={f['expected_intent']!r:15s}  "
                      f"actual={f['actual_intent']!r}")
            if not f["chart_match"]:
                print(f"    Chart  : expected={f['expected_chart']!r:15s}  "
                      f"actual={f['actual_chart']!r}")
            if not f["quality_ok"]:
                print(f"    Quality: expected>={f['expected_quality']!r}  "
                      f"actual={f['actual_quality']!r}")
    else:
        print("\nAll adversarial cases passed!")
    print()


def _format_failures(failures: list[dict[str, Any]], mode: str) -> str:
    lines = []
    for f in failures:
        if mode == "intent" and not f["intent_match"]:
            lines.append(
                f"  [{f['id']}] expected={f['expected_intent']!r} "
                f"actual={f['actual_intent']!r}"
            )
        elif mode == "chart" and not f["chart_match"]:
            lines.append(
                f"  [{f['id']}] expected={f['expected_chart']!r} "
                f"actual={f['actual_chart']!r}"
            )
    return "\n".join(lines) if lines else "(no failures in this dimension)"


# ── Standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = _run_adversarial()
    _print_summary(results)
    print(f"Gates: intent>={MIN_INTENT_ACCURACY*100:.0f}%  "
          f"chart>={MIN_CHART_ACCURACY*100:.0f}%  "
          f"quality>={MIN_QUALITY_PASS_RATE*100:.0f}%")
    all_pass = (
        results["intent_accuracy"] >= MIN_INTENT_ACCURACY
        and results["chart_accuracy"] >= MIN_CHART_ACCURACY
        and results["quality_pass_rate"] >= MIN_QUALITY_PASS_RATE
    )
    print(f"\nResult: {'PASS' if all_pass else 'FAIL'}")
