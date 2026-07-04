"""
Dev-only CLI for testing SQL inference interactively without writing a test.

Usage:
    python -m sqlviz_inference.dev_infer "SELECT mes, SUM(monto) AS total FROM ventas GROUP BY mes"
    python -m sqlviz_inference.dev_infer --file query.sql
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .context import RuntimeContext
from .pipeline import RuntimePipeline
from .result import InferenceResult


def _run(sql: str) -> InferenceResult:
    ctx = RuntimeContext(sql=sql, data=[], schema=[])
    ctx = RuntimePipeline().run(ctx)
    return InferenceResult.from_context(ctx)


def _top_positives(result: InferenceResult, n: int = 5) -> list[dict[str, Any]]:
    """Top N positive signals by contribution, from explanation[]."""
    return sorted(
        result.explanation,
        key=lambda x: float(x.get("contribution", 0.0)),
        reverse=True,
    )[:n]


def _top_penalties(result: InferenceResult, n: int = 5) -> list[dict[str, Any]]:
    """Top N penalties for the winning chart, from score_trace[chart][winner]."""
    chart_trace: dict[str, Any] = result.score_trace.get("chart", {})
    winner_trace: dict[str, Any] = chart_trace.get(result.chart_winner, {})
    penalties: list[dict[str, Any]] = winner_trace.get("penalties_applied", [])
    return sorted(
        penalties,
        key=lambda x: float(x.get("penalty", 0.0)),
        reverse=True,
    )[:n]


def _human_summary(result: InferenceResult) -> str:
    """
    One-line summary built purely from explanation[].
    Lists the top 3 contributing signals and their values.
    Generates no text outside of what the engine already computed.
    """
    if not result.explanation:
        return "(no explanation available)"
    top = sorted(
        result.explanation,
        key=lambda x: float(x.get("contribution", 0.0)),
        reverse=True,
    )[:3]
    parts = [
        f"{item['signal']} ({float(item.get('contribution', 0.0)):.2f})"
        for item in top
    ]
    return "Leading signals: " + ", ".join(parts) + "."


_SEP = "=" * 70


def _print_result(sql: str, result: InferenceResult) -> None:
    print()
    print(_SEP)
    print(f"SQL: {sql.strip()}")
    print(_SEP)
    print()

    print(
        f"intent: {result.intent_winner} "
        f"(score: {result.intent_raw_score:.2f}, quality: {result.intent_quality})"
    )
    print(
        f"chart: {result.chart_winner} "
        f"(score: {result.chart_raw_score:.2f}, quality: {result.chart_quality})"
    )
    print(f"layout: col_span={result.col_span}, row_span={result.row_span}")
    print(f"chart_confidence_gap: {result.chart_confidence_gap:.2f}")
    print()

    positives = _top_positives(result)
    penalties = _top_penalties(result)
    print("Top signals:")
    if positives:
        for sig in positives:
            name = str(sig.get("signal", "?"))
            contrib = float(sig.get("contribution", 0.0))
            print(f"  + {name:<38} (contribution: {contrib:.2f})")
    if penalties:
        for pen in penalties:
            rule = str(pen.get("rule", "?"))
            penalty = float(pen.get("penalty", 0.0))
            print(f"  - {rule:<38} (penalty: {penalty:.2f})")
    if not positives and not penalties:
        print("  (none)")
    print()

    print("Why this visualization:")
    print(f"  {_human_summary(result)}")
    print()

    if result.fallback_applied:
        print(f"Fallback: APPLIED -- {result.fallback_reason}")
    else:
        print("Fallback: not applied")

    if result.errors:
        print("Errors:")
        for err in result.errors:
            print(f"  ! {err}")
    else:
        print("Errors: none")

    print(
        f"Title hint: {result.title!r}  "
        f"(confidence: {result.title_confidence:.4f})"
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m sqlviz_inference.dev_infer",
        description="Run a SQL query through the inference engine and print results.",
    )
    parser.add_argument(
        "sql",
        nargs="?",
        default=None,
        help="SQL string to infer (quote the whole string)",
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        default=None,
        help="Path to a .sql file whose contents will be inferred",
    )
    args = parser.parse_args()

    if args.sql is None and args.file is None:
        parser.error("provide a SQL string as a positional argument or use --file PATH")

    if args.sql is not None and args.file is not None:
        parser.error("provide either a SQL string or --file PATH, not both")

    if args.file is not None:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        sql = path.read_text(encoding="utf-8-sig").strip()
    else:
        sql = str(args.sql).strip()

    if not sql:
        print("Error: SQL is empty.", file=sys.stderr)
        sys.exit(1)

    result = _run(sql)
    _print_result(sql, result)


if __name__ == "__main__":
    main()
