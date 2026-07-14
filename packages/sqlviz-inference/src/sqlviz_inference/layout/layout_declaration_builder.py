from __future__ import annotations

from typing import TYPE_CHECKING

from ..contracts.layout import LayoutDeclaration

if TYPE_CHECKING:
    from ..context import RuntimeContext

# Absolute limits — no panel can go outside these bounds
_COL_SPAN_HARD_MIN = 3
_COL_SPAN_HARD_MAX = 12
_HEIGHT_HARD_MIN = 120
_HEIGHT_HARD_MAX = 720

# Fallback declarations when ReadabilityResult is absent (mirrors LayoutEngine V0.1)
_FALLBACK: dict[str, tuple[int, int, int, int, int, int]] = {
    # chart_type: (col_min, col_pref, col_max, h_min, h_pref, h_max)
    "kpi":            (2,  3,  4,  120, 180, 240),
    "line":           (8, 12, 12,  280, 360, 480),
    "bar":            (6, 12, 12,  240, 360, 480),
    "bar_horizontal": (4,  8, 12,  200, 320, 600),
    "pie":            (4,  6,  8,  280, 350, 440),
    "scatter":        (6,  8, 12,  320, 400, 520),
    "histogram":      (4,  6, 10,  240, 300, 400),
    "table":          (8, 12, 12,  240, 360, 720),
}


class LayoutDeclarationBuilder:
    """
    Builds LayoutDeclaration for a single panel from ReadabilityModel output.

    Each panel declares its own width/height constraints; the dashboard-level
    DashboardLayoutOptimizer consumes all declarations jointly (step 12).

    Falls back to the chart-type lookup table from LayoutEngine V0.1 when
    ReadabilityResult is unavailable (graceful degradation — DOC1 principle).
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.layout_declaration = self._build(context)
        except Exception as e:
            context.errors.append(f"LayoutDeclarationBuilder: {e}")
        return context

    def _build(self, context: RuntimeContext) -> LayoutDeclaration:
        chart = context.chart_winner
        panel_id = getattr(context, "panel_id", "")

        if context.readability_result:
            cand = next(
                (
                    c for c in context.readability_result.by_candidate
                    if c.chart_type == chart
                ),
                None,
            )
            if cand is not None:
                col_min = max(_COL_SPAN_HARD_MIN, cand.col_span_min)
                col_pref = max(col_min, cand.col_span_preferred)
                col_max = min(_COL_SPAN_HARD_MAX, cand.col_span_max)
                h_pref = max(_HEIGHT_HARD_MIN, min(_HEIGHT_HARD_MAX, cand.height_px_recommended))
                h_min = max(_HEIGHT_HARD_MIN, int(h_pref * 0.70))
                h_max = min(_HEIGHT_HARD_MAX, int(h_pref * 1.40))
                return LayoutDeclaration(
                    panel_id=panel_id,
                    col_span_min=col_min,
                    col_span_preferred=col_pref,
                    col_span_max=col_max,
                    height_px_min=h_min,
                    height_px_preferred=h_pref,
                    height_px_max=h_max,
                )

        # Fallback: chart-type lookup (ReadabilityModel wasn't run or chart not found)
        col_min, col_pref, col_max, h_min, h_pref, h_max = _FALLBACK.get(
            chart,
            (4, 6, 12, 240, 360, 600),
        )
        return LayoutDeclaration(
            panel_id=panel_id,
            col_span_min=col_min,
            col_span_preferred=col_pref,
            col_span_max=col_max,
            height_px_min=h_min,
            height_px_preferred=h_pref,
            height_px_max=h_max,
        )
