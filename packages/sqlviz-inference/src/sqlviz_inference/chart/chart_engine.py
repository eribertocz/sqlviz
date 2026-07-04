from __future__ import annotations

from typing import Any

from ..context import ChartCandidate, RuntimeContext
from ..parser.ast_helpers import has_percentile
from ..utils.confidence import confidence_gap, quality_label, should_apply_fallback
from ..utils.math_utils import min_max_normalize
from ..utils.yaml_loader import yaml_loader

# V0 chart types -- exactly 8
V0_CHARTS = [
    "kpi", "line", "bar", "bar_horizontal",
    "pie", "scatter", "histogram", "table",
]

# Feature vector indices used for penalty conditions
PENALTY_FEATURE_INDEX = {
    "has_group_by":              0,
    "has_aggregation":           4,
    "has_temporal_dimension":    31,
    "has_two_numeric_columns":   24,
    "has_single_numeric_column": 23,
    "result_row_count_is_1":     35,
    "result_column_count_is_1":  36,
    "result_is_wide_table":      37,
    "has_outliers":              29,
}


class ChartEngine:
    """
    Selects the best chart type using:
    1. Affinity scores from chart_affinity_matrix.yaml
    2. Penalty rules from chart_penalties.yaml
    3. Fallback rules from fallback_rules.yaml

    V0 supports exactly 8 chart types.
    """

    def __init__(self) -> None:
        self._affinity: dict[str, Any] | None = None
        self._penalties: dict[str, Any] | None = None
        self._fallback: dict[str, Any] | None = None
        self._thresholds: dict[str, Any] | None = None

    @property
    def affinity(self) -> dict[str, Any]:
        if self._affinity is None:
            self._affinity = yaml_loader.load("chart_affinity_matrix.yaml")
        return self._affinity

    @property
    def penalties(self) -> dict[str, Any]:
        if self._penalties is None:
            self._penalties = yaml_loader.load("chart_penalties.yaml")
        return self._penalties

    @property
    def fallback_rules(self) -> dict[str, Any]:
        if self._fallback is None:
            self._fallback = yaml_loader.load("fallback_rules.yaml")
        return self._fallback

    @property
    def thresholds(self) -> dict[str, Any]:
        if self._thresholds is None:
            self._thresholds = yaml_loader.load("thresholds.yaml")
        return self._thresholds

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._score(context)
        except Exception as e:
            return context.with_error("ChartEngine", str(e))

    def _score(self, context: RuntimeContext) -> RuntimeContext:
        fv = context.feature_vector

        # Build intent probability map from intent_scores
        intent_probs: dict[str, float] = {
            score.intent: score.normalized_score
            for score in context.intent_scores
        }

        chart_traces: dict[str, dict[str, Any]] = {}
        raw_scores: dict[str, float] = {}
        # §16.11: track pre-clamp scores for tie-breaking sort
        sort_scores: dict[str, float] = {}

        for chart_type in V0_CHARTS:
            # 1. Affinity score
            chart_affinity = self.affinity.get(chart_type, {})
            affinity_score = sum(
                chart_affinity.get(intent, 0.0) * prob
                for intent, prob in intent_probs.items()
            )

            # 2. Penalty score
            chart_penalties = self.penalties.get(chart_type, {}).get("penalties", {})
            penalty_total = 0.0
            penalties_applied: list[dict[str, Any]] = []

            for feature_name, penalty_weight in chart_penalties.items():
                idx = PENALTY_FEATURE_INDEX.get(feature_name)
                feature_value = fv[idx] if idx is not None and idx < len(fv) else 0.0

                # Derived penalty conditions
                if feature_name == "no_temporal_dimension":
                    feature_value = 1.0 - fv[31]
                elif feature_name == "no_group_by":
                    feature_value = 1.0 - fv[0]
                    # §16.32: QUALIFY + RANK() OVER (ORDER BY DESC) is DuckDB's
                    # idiomatic ranking pattern — no GROUP BY by design.
                    # Suppress the bar_horizontal penalty so ranking intent
                    # correctly maps to bar_horizontal instead of table.
                    if (
                        chart_type == "bar_horizontal"
                        and context.intent_winner == "ranking"
                        and fv[8] > 0.5  # has_window_function
                    ):
                        feature_value = 0.0
                elif feature_name == "high_cardinality":
                    # Mirror the intent engine's data-presence guard:
                    # require ≥ 50 rows (fv[25] > 0.005) so small preview
                    # datasets don't incorrectly trigger pie's cardinality
                    # penalty (§16.x: cardinality false-positive fix).
                    feature_value = (
                        1.0 if (fv[25] > 0.005 and fv[26] > 0.5) else 0.0
                    )
                elif feature_name == "ranking_pattern":
                    feature_value = 1.0 if (fv[2] > 0.5 and fv[3] > 0.5) else 0.0
                elif feature_name == "correlation_intent":
                    feature_value = next(
                        (s.normalized_score for s in context.intent_scores
                         if s.intent == "correlation"),
                        0.0,
                    )
                # §16.24: bar's has_two_numeric_columns penalty was designed to
                # prefer scatter for correlation intent, but it wrongly demotes
                # bar for multi-metric comparison queries (revenue, cost, margin
                # by region).  Suppress the penalty whenever the winning intent
                # is not correlation.
                elif feature_name == "has_two_numeric_columns" and chart_type == "bar":
                    if context.intent_winner != "correlation":
                        feature_value = 0.0

                if feature_value > 0.5:
                    applied_penalty = penalty_weight * feature_value
                    penalty_total += applied_penalty
                    penalties_applied.append({
                        "rule": feature_name,
                        "penalty": round(applied_penalty, 4),
                        "feature_value": round(feature_value, 4),
                    })

            # 3. Final score
            # §16.11: sort by pre-clamp value to preserve differentiation when
            # multiple charts exceed 1.0; store clamped value for display.
            sort_score = max(0.0, affinity_score - penalty_total)
            raw = min(1.0, sort_score)
            raw_scores[chart_type] = raw
            sort_scores[chart_type] = sort_score

            chart_traces[chart_type] = {
                "affinity_score":    round(affinity_score, 4),
                "penalty_total":     round(penalty_total, 4),
                "penalties_applied": penalties_applied,
                "final_score":       round(raw, 4),
            }

        # Normalize clamped scores
        normalized = min_max_normalize(raw_scores)

        # Sort by pre-clamp score descending (§16.11)
        sorted_charts = sorted(sort_scores.items(), key=lambda x: x[1], reverse=True)

        # Add normalized scores to traces
        for chart_type in V0_CHARTS:
            chart_traces[chart_type]["normalized_score"] = round(
                normalized.get(chart_type, 0.0), 4
            )

        # Build ChartCandidate list
        candidates = [
            ChartCandidate(
                chart_type=ct,
                affinity_score=chart_traces[ct]["affinity_score"],
                penalty_total=chart_traces[ct]["penalty_total"],
                final_score=chart_traces[ct]["final_score"],
                normalized_score=chart_traces[ct]["normalized_score"],
                penalties_applied=chart_traces[ct]["penalties_applied"],
            )
            for ct, _ in sorted_charts
        ]

        winner = candidates[0]
        fb_rules = self.fallback_rules
        quality_thresholds = fb_rules.get("quality_thresholds", {})

        # Check fallback
        fallback_applied = False
        fallback_reason = ""
        winner_chart = winner.chart_type

        if should_apply_fallback(
            winner.final_score,
            fb_rules.get("chart", {}).get("min_raw_score", 0.35),
        ):
            fallback_applied = True
            fallback_reason = fb_rules.get("chart", {}).get("message", "")
            winner_chart = fb_rules.get("chart", {}).get("default", "table")

        # §16.33: percentile distribution (quantile_cont / quantile_disc) is
        # best shown as a boxplot, which is not in V0.1 chart types.
        # Force table so the user sees the exact P25/P50/P75 values.
        if (
            context.intent_winner == "distribution"
            and context.ast is not None
            and has_percentile(context.ast)
        ):
            winner_chart = "table"
            fallback_applied = True
            fallback_reason = (
                "Percentile distribution — boxplot not available in V0.1; showing raw data"
            )

        # Determine alternatives to show
        gap = confidence_gap(normalized)
        ql = quality_label(winner.final_score, quality_thresholds)

        if ql == "high" and gap >= 0.60:
            n_alternatives = 0
        elif ql == "high" and gap < 0.60:
            n_alternatives = 2
        elif ql in ("medium", "low") and gap >= 0.60:
            n_alternatives = 1
        else:
            n_alternatives = 0

        alternatives = [
            {"chart": c.chart_type, "raw_score": c.final_score}
            for c in candidates[1:n_alternatives + 1]
            if c.final_score > 0.0
        ]

        context.chart_candidates = candidates
        context.chart_winner = winner_chart
        context.chart_raw_score = winner.final_score
        context.chart_normalized_score = winner.normalized_score
        context.chart_confidence_gap = gap
        context.chart_quality = ql
        context.chart_alternatives = alternatives
        context.fallback_applied = fallback_applied
        context.fallback_reason = fallback_reason
        context.score_trace["chart"] = chart_traces

        return context
