from __future__ import annotations

from dataclasses import dataclass, field

DASHBOARD_ROLES = frozenset({
    "resumen_ejecutivo",
    "historia_principal",
    "explicacion_secundaria",
    "diagnostico",
    "tabla_de_detalle",
    "control",
})


@dataclass
class LayoutDeclaration:
    """
    Each panel declares its own layout needs based on ReadabilityModel
    output and chart type. DashboardLayoutOptimizer consumes this to
    place all panels jointly rather than one at a time.
    """

    panel_id: str
    col_span_min: int = 4
    col_span_preferred: int = 6
    col_span_max: int = 12
    height_px_min: int = 240
    height_px_preferred: int = 360
    height_px_max: int = 600


@dataclass
class DashboardRole:
    """
    Narrative role of a panel within the dashboard.
    Role influences position priority in DashboardLayoutOptimizer:
    resumen_ejecutivo and historia_principal rank highest.
    """

    panel_id: str
    role: str = "historia_principal"   # one of DASHBOARD_ROLES
    priority: int = 5                  # lower = placed earlier / higher


@dataclass
class PanelPlacement:
    panel_id: str
    row: int
    col_offset: int
    col_span: int
    height_px: int


@dataclass
class DashboardPlan:
    """
    Complete placement decision for all panels in a dashboard.
    Output of DashboardLayoutOptimizer; scored by DashboardObjective.
    """

    placements: list[PanelPlacement] = field(default_factory=list)
    total_rows: int = 0
    utility_score: float = 0.0   # from DashboardObjective
