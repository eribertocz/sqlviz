"""Benchmark release gate — DOC5 Section 14.5."""
from __future__ import annotations

from .benchmark.run_benchmark import run_benchmark

# These thresholds are the RELEASE GATE.
# Never merge code that drops below these values.
MIN_INTENT_ACCURACY = 0.85
MIN_CHART_ACCURACY = 0.85
MIN_QUALITY_PASS_RATE = 0.80


class TestBenchmarkReleaseGate:

    def test_intent_accuracy_above_threshold(self) -> None:
        results = run_benchmark()
        assert results["intent_accuracy"] >= MIN_INTENT_ACCURACY, (
            f"Intent accuracy {results['intent_accuracy'] * 100:.1f}% "
            f"is below the release gate of {MIN_INTENT_ACCURACY * 100:.0f}%.\n"
            f"Failures: {results['failures']}"
        )

    def test_chart_accuracy_above_threshold(self) -> None:
        results = run_benchmark()
        assert results["chart_accuracy"] >= MIN_CHART_ACCURACY, (
            f"Chart accuracy {results['chart_accuracy'] * 100:.1f}% "
            f"is below the release gate of {MIN_CHART_ACCURACY * 100:.0f}%.\n"
            f"Failures: {results['failures']}"
        )

    def test_quality_pass_rate_above_threshold(self) -> None:
        results = run_benchmark()
        assert results["quality_pass_rate"] >= MIN_QUALITY_PASS_RATE, (
            f"Quality pass rate {results['quality_pass_rate'] * 100:.1f}% "
            f"is below the release gate of {MIN_QUALITY_PASS_RATE * 100:.0f}%."
        )
