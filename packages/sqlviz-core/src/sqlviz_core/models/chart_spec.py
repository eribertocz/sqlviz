from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChartSpec:
    """Serializable chart specification sent from backend to frontend.

    The backend (VizEngine) produces this; the frontend routes by engine name
    to EChartsRenderer or PlotlyRenderer (DOC3 Section 9, DOC6 Section 5.3).
    """

    engine: str       # "echarts" | "plotly"
    chart_type: str   # "line" | "bar" | "bar_horizontal" | "kpi" | "table" | ...
    options: dict[str, object] = field(default_factory=dict)
    # options is the engine-specific JSON payload:
    # ECharts → full ECharts `option` object
    # Plotly  → {traces: [...], layout: {...}}
