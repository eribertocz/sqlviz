from __future__ import annotations

from typing import TYPE_CHECKING

from ..contracts.readability import CandidateReadability, ReadabilityResult
from ..utils.sqlviz_logging import get_logger

_log = get_logger("readability_model")

if TYPE_CHECKING:
    from ..context import RuntimeContext

# Perceptual hierarchy baseline (Cleveland & McGill, Heer & Bostock)
_BASE_LEGIBILITY: dict[str, float] = {
    "kpi":            1.00,   # single value — perfect clarity
    "line":           0.93,   # position on common scale
    "bar":            0.92,
    "bar_horizontal": 0.94,   # handles long labels better than vertical
    "pie":            0.88,   # angle encoding, acceptable for ≤ 3 slices
    "scatter":        0.82,   # 2D position, moderate
    "histogram":      0.87,
    "table":          0.78,   # accurate but requires active reading
}

# Default col_span (min, preferred, max)
_COL_SPAN: dict[str, tuple[int, int, int]] = {
    "kpi":            (2, 3, 4),
    "line":           (6, 8, 12),
    "bar":            (4, 6, 12),
    "bar_horizontal": (4, 6, 12),
    "pie":            (4, 6, 8),
    "scatter":        (6, 8, 12),
    "histogram":      (4, 6, 10),
    "table":          (8, 12, 12),
}

# Base height in pixels
_BASE_HEIGHT: dict[str, int] = {
    "kpi":            180,
    "line":           360,
    "bar":            300,
    "bar_horizontal": 300,   # adjusted dynamically based on cardinality
    "pie":            350,
    "scatter":        400,
    "histogram":      300,
    "table":          360,
}


class ReadabilityModel:
    """
    Translates DataProfile statistics into readability recommendations per
    chart candidate. Runs BEFORE ScoringModel (DOC10 §7 step 8).

    Outputs CandidateReadability per candidate:
      - col_span_min/preferred/max — grid width recommendation
      - height_px_recommended      — ideal panel height
      - legibility_score [0, 1]    — visual clarity given the data

    Legibility is penalized for:
      - Many categories on bar/pie (angle/length discrimination harder)
      - Long labels on vertical bar (rotation → illegibility)
      - Many rows on table (scrolling required)
      - Many series on line chart (color discrimination harder)
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.readability_result = self._build(context)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            context.errors.append(f"ReadabilityModel: {e}")
        return context

    def _build(self, context: RuntimeContext) -> ReadabilityResult:
        eliminated = set()
        if context.constraint_report:
            eliminated = {v.chart_type for v in context.constraint_report.eliminated}

        by_candidate = [
            self._score(c.chart_type, context)
            for c in context.chart_candidates
            if c.chart_type not in eliminated
        ]
        return ReadabilityResult(by_candidate=by_candidate)

    def _score(self, chart_type: str, context: RuntimeContext) -> CandidateReadability:
        row_count = (
            context.data_profile.row_count if context.data_profile else len(context.data)
        )
        cat_cardinality, max_label_len, n_numeric = self._data_stats(context)
        n_series = max(1, n_numeric)

        # col_span
        cs_min, cs_pref, cs_max = self._col_span(chart_type, cat_cardinality, max_label_len)

        # height
        height = self._height(chart_type, cat_cardinality, row_count)

        # legibility
        legibility = self._legibility(
            chart_type, cat_cardinality, max_label_len, n_series, row_count
        )

        return CandidateReadability(
            chart_type=chart_type,
            col_span_min=cs_min,
            col_span_preferred=cs_pref,
            col_span_max=cs_max,
            height_px_recommended=height,
            legibility_score=round(legibility, 4),
        )

    # ── Helpers ────────────────────────────────────────────────────────────

    def _data_stats(self, context: RuntimeContext) -> tuple[int, int, int]:
        """Return (cat_cardinality, max_label_length, n_numeric_metric_cols)."""
        if context.data_profile and context.data_profile.column_profiles:
            cat_card = 1
            max_lbl = 5
            for cp in context.data_profile.column_profiles:
                if not cp.is_numeric:
                    cat_card = max(1, cp.cardinality)
                    max_lbl = cp.max_label_length
                    break
        elif context.data:
            first_row = context.data[0]
            cat_card = len(context.data)
            max_lbl = max((len(str(v)) for v in first_row.values()), default=5)
        else:
            cat_card = 1
            max_lbl = 5

        n_metric = 0
        if context.column_roles:
            n_metric = sum(1 for r in context.column_roles.roles if r.role == "metric")
        elif context.schema:
            _NUMERIC = frozenset({
                "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
                "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
            })
            _ID_SFX = ("_id", "_key")
            for col in context.schema:
                nt = col.type.upper().split("(")[0].strip()
                nl = col.name.lower()
                if nt in _NUMERIC and not any(nl.endswith(s) for s in _ID_SFX) and nl != "id":
                    n_metric += 1

        return cat_card, max_lbl, max(1, n_metric)

    def _col_span(
        self, chart_type: str, cardinality: int, max_label_len: int
    ) -> tuple[int, int, int]:
        cs_min, cs_pref, cs_max = _COL_SPAN.get(chart_type, (4, 6, 12))

        if chart_type == "bar":
            if cardinality > 10:
                cs_min = max(cs_min, 8)
                cs_pref = max(cs_pref, 10)
            elif cardinality > 6:
                cs_min = max(cs_min, 6)
                cs_pref = max(cs_pref, 8)
            # Long labels need more horizontal space
            if max_label_len > 8:
                cs_pref = min(cs_max, cs_pref + 2)

        elif chart_type == "bar_horizontal":
            # Long labels handled gracefully in horizontal mode
            if cardinality > 15:
                cs_pref = max(cs_pref, 8)
            if max_label_len > 12:
                cs_min = max(cs_min, 6)
                cs_pref = max(cs_pref, 8)

        elif chart_type == "line":
            # Wide time series need more horizontal room
            if cardinality > 20:
                cs_pref = max(cs_pref, 10)

        return cs_min, cs_pref, cs_max

    def _height(self, chart_type: str, cardinality: int, row_count: int) -> int:
        base = _BASE_HEIGHT.get(chart_type, 360)

        if chart_type == "bar_horizontal":
            # 32px per category, capped
            dynamic = max(200, min(600, 80 + cardinality * 32))
            return dynamic

        if chart_type == "table":
            rows_shown = min(row_count, 20)
            return max(240, min(600, 120 + rows_shown * 28))

        if chart_type == "kpi":
            return base

        return base

    def _legibility(
        self,
        chart_type: str,
        cardinality: int,
        max_label_len: int,
        n_series: int,
        row_count: int,
    ) -> float:
        score = _BASE_LEGIBILITY.get(chart_type, 0.80)

        if chart_type == "bar":
            # More categories → harder to read
            excess = max(0, cardinality - 5)
            score -= 0.04 * excess
            # Long labels on vertical bar require rotation
            if max_label_len > 10:
                score -= 0.08
            elif max_label_len > 7:
                score -= 0.04

        elif chart_type == "bar_horizontal":
            excess = max(0, cardinality - 5)
            score -= 0.02 * excess   # gentler penalty — horizontal handles many
            if max_label_len > 20:
                score -= 0.05

        elif chart_type == "pie":
            excess = max(0, cardinality - 2)
            score -= 0.06 * excess   # each additional slice reduces clarity

        elif chart_type == "line":
            series_excess = max(0, n_series - 1)
            score -= 0.05 * series_excess   # each additional series adds a color track
            if row_count > 50:
                score -= 0.04   # dense time series harder to read fine points

        elif chart_type == "scatter":
            if row_count > 100:
                score -= 0.06   # overplotting
            elif row_count > 50:
                score -= 0.03

        elif chart_type == "table":
            row_excess = max(0, row_count - 10)
            score -= 0.02 * (row_excess // 5)   # every 5 extra rows: -0.02
            col_excess = max(0, cardinality - 3)
            score -= 0.02 * col_excess

        elif chart_type == "histogram":
            if row_count > 100:
                score -= 0.03   # many bins may overlap labels

        return max(0.10, min(1.00, score))
