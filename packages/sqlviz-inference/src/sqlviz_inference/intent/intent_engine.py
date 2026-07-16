from __future__ import annotations

from typing import Any

from ..context import IntentScore, RuntimeContext
from ..parser.ast_helpers import (
    get_column_names_from_select,
    has_part_of_whole_pattern,
    has_percentile,
    has_qualify,
)
from ..semantic.fuzzy_match import normalize_name
from ..utils.confidence import confidence_gap, quality_label
from ..utils.math_utils import min_max_normalize
from ..utils.sqlviz_logging import get_logger
from ..utils.yaml_loader import yaml_loader

_log = get_logger("intent_engine")

# Feature vector index mapping — used to extract values from feature_vector by name
FEATURE_INDEX = {
    "has_group_by":              0,
    "has_order_by":              1,
    "has_order_by_desc":         2,
    "has_limit":                 3,
    "has_aggregation":           4,
    "has_sum":                   5,
    "has_count":                 6,
    "has_avg":                   7,
    "has_window_function":       8,
    "has_cte":                   9,
    "has_join":                  10,
    "has_where":                 11,
    "group_by_column_count":     12,
    "select_column_count":       13,
    "has_subquery":              14,
    "has_partition_by":          15,
    "has_case_when":             16,
    "has_distinct":              17,
    "has_date_column":           18,
    "has_numeric_column":        19,
    "has_string_column":         20,
    "numeric_column_ratio":      21,
    "date_column_ratio":         22,
    "has_single_numeric_column": 23,
    "has_two_numeric_columns":   24,
    "row_count_normalized":      25,
    "cardinality_ratio":         26,
    "temporal_cardinality":      27,
    "trend_strength":            28,
    "has_outliers":              29,
    "has_revenue_metric":        30,
    "has_temporal_dimension":    31,
    "has_geographic_dimension":  32,
    "has_product_entity":        33,
    "has_customer_entity":       34,
    "result_row_count_is_1":     35,
    "result_column_count_is_1":  36,
    "result_is_wide_table":      37,
}

# ── §16.21 Part-of-whole signal constants ─────────────────────────────────────
# Column names (normalized) that are STRONG evidence of a share/composition query.
_POW_POSITIVE_NAMES: frozenset[str] = frozenset([
    "participacion",
    "participaci_n",   # participación (accented) → normalized form
    "share",
    "share_of_total",
    "pct_total",
    "porcentaje_total",
    "parte_total",
])
# Tokens within a compound column name that signal part-of-whole intent.
_POW_POSITIVE_TRIGGER: frozenset[str] = frozenset([
    "participacion",
    "participaci_n",
])

# Column names (normalized) that are evidence of a RATE/RATIO — NOT part-of-whole.
# These explicitly suppress composition intent.
_POW_NEGATIVE_NAMES: frozenset[str] = frozenset([
    "margen_pct",
    "ratio_cobrado_facturado",
])
# Tokens within a compound column name that signal a rate (negative for composition).
_POW_NEGATIVE_TRIGGER: frozenset[str] = frozenset([
    "tasa",          # tasa_mora, tasa_pago → rate
    "recuperacion",  # recuperacion_pct → recovery rate
    "recuperaci_n",  # accented form
    "conversion",    # conversion_rate
    "eficiencia",    # efficiency metric
    "cumplimiento",  # compliance rate
    "ratio",         # ratio_cobrado_facturado
])


def _get_feature(fv: list[float], name: str) -> float:
    idx = FEATURE_INDEX.get(name)
    if idx is None:
        return 0.0
    return fv[idx] if idx < len(fv) else 0.0


def _get_all_column_names(context: RuntimeContext) -> set[str]:
    """Return normalized column names from schema + SELECT aliases."""
    names: set[str] = set()
    for col in context.schema:
        names.add(normalize_name(col.name))
    if context.ast is not None:
        for name in get_column_names_from_select(context.ast):
            names.add(normalize_name(name))
    return names


def _compute_part_of_whole_score(context: RuntimeContext) -> float:
    """
    Structural + semantic score for 'part-of-total' evidence (§16.21).

    Returns a value in [-1.0, 1.0]:
      +1.0  structural AST signal x / AGG(x) OVER () (DOC4 §19.4 share formula)
      +0.6  strong positive column name  (participacion, share, pct_total …)
       0.0  neutral — no evidence either way
      -0.8  negative column name (tasa_mora, conversion_rate, eficiencia …)

    Signals combine additively; result is clamped to [-1.0, 1.0].
    A negative score actively reduces composition intent (not merely absent boost).
    """
    score = 0.0

    if context.ast is not None and has_part_of_whole_pattern(context.ast):
        score += 1.0

    all_names = _get_all_column_names(context)
    has_positive = False
    has_negative = False
    for norm_name in all_names:
        tokens = frozenset(norm_name.split("_"))
        if norm_name in _POW_POSITIVE_NAMES or tokens & _POW_POSITIVE_TRIGGER:
            has_positive = True
        elif norm_name in _POW_NEGATIVE_NAMES or tokens & _POW_NEGATIVE_TRIGGER:
            has_negative = True

    if has_positive:
        score += 0.6
    if has_negative:
        score -= 0.8

    return max(-1.0, min(1.0, score))


def _compute_monotonic_decrease_score(context: RuntimeContext) -> float:
    """
    Funnel signal: fraction of consecutive metric pairs that decrease,
    when the result is ordered ascending (§16.29).

    Guards:
    - has_order_by=1: requires an explicit sequence ordering
    - has_order_by_desc=0: DESC ordering signals ranking/comparison, not a funnel step sequence
    - >= 3 rows: avoids coincidental signals from tiny results

    Returns a value in [0.0, 1.0] (fraction of decreasing pairs).
    """
    fv = context.feature_vector
    if _get_feature(fv, "has_order_by") < 0.5:
        return 0.0
    if _get_feature(fv, "has_order_by_desc") > 0.5:
        return 0.0
    if not context.data or len(context.data) < 3:
        return 0.0
    numeric_values: list[float] = []
    for row in context.data:
        for v in row.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                numeric_values.append(float(v))
                break
    if len(numeric_values) < 3:
        return 0.0
    n_pairs = len(numeric_values) - 1
    n_decreasing = sum(1 for a, b in zip(numeric_values, numeric_values[1:]) if a > b)
    return n_decreasing / n_pairs


def _compute_distinct_entity_count_signal(fv: list[float]) -> float:
    """
    Retention signal: COUNT(DISTINCT <entity>) over a temporal dimension (§16.30).
    Requires has_count=1, has_distinct=1, has_customer_entity=1,
    has_temporal_dimension=1 — pure feature-vector check, no AST walk.
    Returns 1.0 when all four hold, else 0.0.
    """
    if (
        _get_feature(fv, "has_count") > 0.5
        and _get_feature(fv, "has_distinct") > 0.5
        and _get_feature(fv, "has_customer_entity") > 0.5
        and _get_feature(fv, "has_temporal_dimension") > 0.5
    ):
        return 1.0
    return 0.0


def _compute_derived_features(
    fv: list[float], context: RuntimeContext
) -> dict[str, float]:
    """
    Compute derived features not directly in the feature vector.
    These are boolean inversions or combinations used in YAML rules.
    """
    return {
        # Inversions
        "no_group_by":           1.0 - _get_feature(fv, "has_group_by"),
        "no_aggregation":        1.0 - _get_feature(fv, "has_aggregation"),
        "no_temporal_dimension": 1.0 - _get_feature(fv, "has_temporal_dimension"),
        "no_order_by_desc":      1.0 - _get_feature(fv, "has_order_by_desc"),
        # §16.33: suppress no_numeric_column when percentile functions are present —
        # quantile_cont/disc produce numeric output by definition, even without schema.
        "no_numeric_column": (
            0.0
            if context.ast is not None and has_percentile(context.ast)
            else 1.0 - _get_feature(fv, "has_numeric_column")
        ),
        "no_case_when":          1.0 - _get_feature(fv, "has_case_when"),
        "no_customer_entity":    1.0 - _get_feature(fv, "has_customer_entity"),
        # Combinations (§16.10: order_desc_and_limit was missing from spec — added here)
        # §16.32: QUALIFY + window + ORDER BY DESC is DuckDB's idiomatic equivalent
        # of LIMIT for ranking window functions (RANK/ROW_NUMBER/DENSE_RANK).
        "order_desc_and_limit": (
            1.0
            if _get_feature(fv, "has_order_by_desc") > 0.5
            and (
                _get_feature(fv, "has_limit") > 0.5
                or (
                    _get_feature(fv, "has_window_function") > 0.5
                    and context.ast is not None
                    and has_qualify(context.ast)
                )
            )
            else 0.0
        ),
        # Threshold-based derived booleans.
        # Both require real data (row_count_normalized > 0) to avoid false
        # signals when no result rows are available.
        # high_cardinality additionally requires ≥ 50 rows (0.005 threshold)
        # so that small benchmark/preview datasets with all-distinct categorical
        # values do not incorrectly trigger the "many categories" penalty on
        # composition (§16.x: cardinality false-positive fix).
        "high_cardinality": (
            1.0
            if (
                _get_feature(fv, "row_count_normalized") > 0.005  # ≥ 50 rows
                and _get_feature(fv, "cardinality_ratio") > 0.5
            )
            else 0.0
        ),
        # low_cardinality fires when data IS present and either:
        #   a) ratio < 15 % (large dataset, genuinely few distinct categories), or
        #   b) estimated distinct group count ≤ 3 (tiny dataset with few groups,
        #      typical of a composition result like payment_method or tier).
        # Guards (§16.23, §16.26):
        #   - cardinality_ratio > 0.0: when no VARCHAR column exists the
        #     function returns 0.0, which would falsely satisfy < 0.15.
        #   - no_temporal_dimension: cohort/trend queries that include a
        #     low-cardinality secondary dimension (e.g. "segmento" with 2 values)
        #     must not be pulled toward composition just because the segment column
        #     has few distinct values.
        "low_cardinality": (
            1.0
            if (
                _get_feature(fv, "row_count_normalized") > 0.0
                and _get_feature(fv, "cardinality_ratio") > 0.0   # §16.23
                and _get_feature(fv, "has_temporal_dimension") < 0.5  # §16.26
                and (
                    _get_feature(fv, "cardinality_ratio") < 0.15
                    or (
                        _get_feature(fv, "cardinality_ratio")
                        * _get_feature(fv, "row_count_normalized")
                        * 10_000
                        <= 3.0
                    )
                )
            )
            else 0.0
        ),
        "no_count":             1.0 - _get_feature(fv, "has_count"),
        "multiple_rows":        1.0 - _get_feature(fv, "result_row_count_is_1"),
        "single_numeric_column": _get_feature(fv, "has_single_numeric_column"),
        "high_col_count":       1.0 if _get_feature(fv, "select_column_count") > 0.3 else 0.0,
        # §16.22: was `> 0.4` (strict), which silently required ≥ 3 GROUP BY columns.
        # Fixed to `>= 0.4` so that exactly 2 GROUP BY columns (dim12 = 2/5 = 0.4) fires.
        "group_by_count_gte_2": 1.0 if _get_feature(fv, "group_by_column_count") >= 0.4 else 0.0,
        "has_outliers_detected": _get_feature(fv, "has_outliers"),
        # §16.21: structural + semantic part-of-whole evidence.
        # Value in [-1.0, 1.0]; used as composition weight — negative values
        # actively reduce composition score for rate/ratio column names.
        "part_of_whole_score": _compute_part_of_whole_score(context),
        # §16.29: funnel step-drop signal — fraction of consecutive metric pairs
        # that decrease in an ASC-ordered result. Guards against ranking queries
        # (has_order_by_desc=1) and noise (< 3 rows).
        "is_monotonic_decreasing": _compute_monotonic_decrease_score(context),
        # §16.30: COUNT(DISTINCT <entity>) over time — precise retention signal
        # that fires only when all four structural conditions hold simultaneously.
        "distinct_entity_count_over_time": _compute_distinct_entity_count_signal(fv),
        # §16.33: percentile/quantile aggregation — signals distribution intent
        # and suppresses comparison/composition/anomaly misclassifications.
        "has_percentile": (
            1.0
            if context.ast is not None and has_percentile(context.ast)
            else 0.0
        ),
    }


class IntentEngine:
    """
    Scores 12 analytical intents from the feature vector.
    Reads all weights from intent_rules.yaml.
    Never hardcodes numerical constants.
    """

    def __init__(self) -> None:
        self._rules: dict[str, Any] | None = None

    @property
    def rules(self) -> dict[str, Any]:
        if self._rules is None:
            self._rules = yaml_loader.load("intent_rules.yaml")
        return self._rules

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._score(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            return context.with_error("IntentEngine", str(e))

    def _score(self, context: RuntimeContext) -> RuntimeContext:
        fv = context.feature_vector
        derived = _compute_derived_features(fv, context)

        # Build unified feature lookup
        all_features = {name: _get_feature(fv, name) for name in FEATURE_INDEX}
        all_features.update(derived)

        raw_scores: dict[str, float] = {}
        signal_traces: dict[str, dict[str, Any]] = {}

        for intent_name, intent_config in self.rules.items():
            weights = intent_config.get("weights", {})
            penalties = intent_config.get("penalties", {})
            boosts = intent_config.get("boosts", {})

            # Positive score
            pos_score = 0.0
            signals: dict[str, dict[str, Any]] = {}
            for feature_name, weight in weights.items():
                value = all_features.get(feature_name, 0.0)
                contribution = weight * value
                pos_score += contribution
                signals[feature_name] = {
                    "weight": weight,
                    "value": value,
                    "contribution": round(contribution, 4),
                }

            # Penalties — trigger when feature value > 0.5
            penalty_total = 0.0
            for feature_name, penalty in penalties.items():
                value = all_features.get(feature_name, 0.0)
                if value > 0.5:
                    penalty_total += penalty * value

            # Boosts — multipliers applied when derived feature > 0.5
            boost_multiplier = 1.0
            for boost_name, multiplier in boosts.items():
                if all_features.get(boost_name, 0.0) > 0.5:
                    boost_multiplier = multiplier

            raw = max(0.0, min(1.0, (pos_score - penalty_total) * boost_multiplier))
            raw_scores[intent_name] = raw
            signal_traces[intent_name] = {
                "raw_score": round(raw, 4),
                "positive_score": round(pos_score, 4),
                "penalty_total": round(penalty_total, 4),
                "boost_multiplier": boost_multiplier,
                "signals": signals,
            }

        # Normalize scores
        normalized = min_max_normalize(raw_scores)

        # Sort by raw score descending
        sorted_intents = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)

        intent_scores = [
            IntentScore(
                intent=name,
                raw_score=raw_scores[name],
                normalized_score=normalized[name],
                signals=signal_traces[name]["signals"],
            )
            for name, _ in sorted_intents
        ]

        winner = intent_scores[0]
        thresholds = yaml_loader.load("thresholds.yaml")

        context.intent_scores = intent_scores
        context.intent_winner = winner.intent
        context.intent_raw_score = winner.raw_score
        context.intent_normalized_score = winner.normalized_score
        context.intent_confidence_gap = confidence_gap(normalized)
        context.intent_quality = quality_label(
            winner.raw_score,
            thresholds.get("quality_thresholds"),
        )

        context.score_trace["intent"] = signal_traces

        context.explanation = [
            {
                "module": "IntentEngine",
                "signal": feat,
                "weight": sig["weight"],
                "value": sig["value"],
                "contribution": sig["contribution"],
            }
            for feat, sig in signal_traces[winner.intent]["signals"].items()
            if sig["contribution"] > 0.01
        ]

        return context
