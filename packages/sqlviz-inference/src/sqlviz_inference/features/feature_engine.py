from __future__ import annotations

from ..context import RuntimeContext
from ..utils.sqlviz_logging import get_logger
from .column_features import compute as compute_column_features
from .data_statistics import (
    compute_dim25_row_count,
    compute_dim26_cardinality,
    compute_dim27_temporal_cardinality,
    compute_dim28_trend_strength,
    compute_dim29_has_outliers,
    compute_dim38_trend_direction,
)
from .result_shape import compute as compute_result_shape

_log = get_logger("feature_engine")


class FeatureEngine:
    """
    Computes the complete 39-dimension feature vector V0.
    Fills dims 18-29 and 35-38 (dims 0-17 already filled by Parser).
    Dims 30-34 are reserved for the Semantic Engine.
    Uses lazy evaluation — expensive features only when data is available.
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._compute(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            return context.with_error("FeatureEngine", str(e))

    def _compute(self, context: RuntimeContext) -> RuntimeContext:
        fv = context.feature_vector[:]  # work on a copy

        # ── Column type features (dims 18-24) ─────────────────────────────
        if context.has_schema:
            col_feats = compute_column_features(context.schema)
            for i, val in enumerate(col_feats):
                fv[18 + i] = val

        # ── Data statistics (dims 25-29) ──────────────────────────────────
        if context.has_data:
            fv[25] = compute_dim25_row_count(context.data)

        if context.has_data and context.row_count > 1:
            fv[26] = compute_dim26_cardinality(context.data, context.schema)

        if context.has_data and context.row_count >= 3:
            fv[27] = compute_dim27_temporal_cardinality(
                context.data, context.schema
            )
            fv[28] = compute_dim28_trend_strength(
                context.data, context.schema
            )
            fv[29] = compute_dim29_has_outliers(
                context.data, context.schema
            )
            fv[38] = compute_dim38_trend_direction(
                context.data, context.schema
            )

        # dims 30-34 → reserved for Semantic Engine

        # ── Result shape features (dims 35-37) ────────────────────────────
        if context.has_data:
            shape = compute_result_shape(context.data)
            fv[35] = shape[0]
            fv[36] = shape[1]
            fv[37] = shape[2]

        context.feature_vector = fv
        return context
