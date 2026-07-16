from __future__ import annotations

from ..context import RuntimeContext
from ..utils.sqlviz_logging import get_logger

_log = get_logger("layout_engine")

# Chart type -> default layout (col_span, row_span)
# row_span=1 reserved for KPI (compact number cards that need no visual height).
# All chart types that render a visual (axes, marks, data points) use row_span=2
# so the ECharts container gets enough height to be readable.
CHART_DEFAULT_LAYOUT: dict[str, tuple[int, int]] = {
    "kpi":            (3,  1),
    "line":           (12, 2),
    "bar":            (12, 2),
    "bar_horizontal": (12, 2),
    "pie":            (6,  2),
    "scatter":        (6,  2),
    "histogram":      (6,  2),
    "table":          (12, 2),
}

# Fixed pixel heights per chart type (40px Grafana grid unit standard).
# Dynamic charts (bar_horizontal, table) compute their height from row_count.
_FIXED_HEIGHT: dict[str, int] = {
    "kpi":       120,
    "line":      360,
    "bar":       360,
    "pie":       320,
    "scatter":   440,
    "histogram": 360,
}
_FALLBACK_HEIGHT = 360

# (intent, chart_type) -> col_span override
INTENT_LAYOUT_ADJUSTMENTS: dict[tuple[str, str], int] = {
    ("trend",       "line"):           12,
    ("trend",       "bar"):            12,
    ("ranking",     "bar_horizontal"): 8,
    ("composition", "pie"):            4,
    ("kpi",         "kpi"):            3,
    ("detail",      "table"):          12,
    ("comparison",  "bar"):            12,
    ("comparison",  "bar_horizontal"): 8,
}


class LayoutEngine:
    """
    Assigns CSS Grid spans to panels.

    Rules (in priority order):
    1. Chart type default layout
    2. Intent-based adjustments
    3. Data characteristic adjustments
    4. Always clamp to valid range [3-12] col, [1-3] row
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            return self._assign_layout(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            return context.with_error("LayoutEngine", str(e))

    def _assign_layout(self, context: RuntimeContext) -> RuntimeContext:
        chart = context.chart_winner
        intent = context.intent_winner
        fv = context.feature_vector

        # Priority 1 — Chart type default
        col_span, row_span = CHART_DEFAULT_LAYOUT.get(chart, (12, 1))

        # Priority 2 — Intent adjustment
        adjusted_col = INTENT_LAYOUT_ADJUSTMENTS.get((intent, chart))
        if adjusted_col is not None:
            col_span = adjusted_col

        # Priority 3 — Data characteristic adjustments
        row_count = context.row_count

        # Large tables need more vertical space
        if chart == "table" and row_count > 100:
            row_span = min(row_span + 1, 3)

        # Many categories need more horizontal space
        cardinality = fv[26] if len(fv) > 26 else 0.0
        if chart in ("bar", "bar_horizontal") and cardinality > 0.30:
            col_span = 12

        # KPI with strong trend signal can use slightly more space
        if chart == "kpi" and fv[28] > 0.5:
            col_span = 4

        # Clamp to valid range
        col_span = max(3, min(col_span, 12))
        row_span = max(1, min(row_span, 3))

        importance = self._compute_importance(context, col_span, row_span)
        panel_height_px = self._calculate_height(chart, row_count)

        context.col_span = col_span
        context.row_span = row_span
        context.layout_importance = importance
        context.panel_height_px = panel_height_px

        context.score_trace["layout"] = {
            "chart_type":      chart,
            "intent":          intent,
            "col_span":        col_span,
            "row_span":        row_span,
            "panel_height_px": panel_height_px,
            "importance":      round(importance, 4),
            "adjustments": {
                "intent_adjustment": adjusted_col,
                "row_count":         row_count,
                "cardinality":       round(cardinality, 4),
            },
        }

        return context

    def _compute_importance(
        self,
        context: RuntimeContext,
        col_span: int,
        row_span: int,
    ) -> float:
        """
        importance =
            0.40 x size_score      (how much space it takes)
            0.30 x intent_strength (how confident the intent is)
            0.20 x metric_weight   (semantic importance of metric)
            0.10 x position_pref   (KPIs always rank high)
        """
        size_score = (col_span * row_span) / (12 * 3)

        intent_strength = context.intent_raw_score

        fv = context.feature_vector
        metric_weight = 0.5
        if len(fv) > 30 and fv[30] > 0.5:
            metric_weight = 1.0
        elif len(fv) > 34 and fv[34] > 0.5:
            metric_weight = 0.8

        position_pref = 1.0 if context.chart_winner == "kpi" else 0.5

        importance = (
            0.40 * size_score
            + 0.30 * intent_strength
            + 0.20 * metric_weight
            + 0.10 * position_pref
        )

        return max(0.0, min(1.0, importance))

    @staticmethod
    def _calculate_height(chart: str, row_count: int) -> int:
        """Return panel height in px (40px Grafana grid unit standard).

        Fixed charts use the constant from _FIXED_HEIGHT.
        Dynamic charts clamp their row-based formula:
          bar_horizontal: 120px overhead + 40px/bar, range [280, 600]
          table:           80px overhead + 40px/row, range [280, 720]
        """
        if chart in _FIXED_HEIGHT:
            return _FIXED_HEIGHT[chart]
        if chart == "bar_horizontal":
            return max(280, min(600, 120 + row_count * 40))
        if chart == "table":
            return max(280, min(720, 80 + row_count * 40))
        return _FALLBACK_HEIGHT
