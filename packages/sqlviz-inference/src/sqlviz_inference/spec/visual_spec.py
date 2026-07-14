from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VisualSpec:
    """
    Exact render contract delivered to EChartsRenderer.
    The frontend reads this — it infers nothing from raw data.
    Built by VisualSpecBuilder using the chart_winner from ChartEngine.
    """

    chart_type: str            # one of V0_CHARTS
    x_field: str | None        # category / time axis; None for kpi, table
    y_fields: list[str]        # metric field(s); all cols for table
    orientation: str           # "vertical" | "horizontal" | "none"
    sort_order: str            # "asc" | "desc" | "none"
    color_field: str | None    # multi-series grouping (V0.2+), None now
    stack: bool                # stacked series (V0.2+), False now
    number_format: str         # "default" | "percent" | "currency"
    tooltip_fields: list[str] = field(default_factory=list)
