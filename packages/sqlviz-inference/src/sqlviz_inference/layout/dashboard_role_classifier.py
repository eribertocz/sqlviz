from __future__ import annotations

from typing import TYPE_CHECKING

from ..contracts.layout import DashboardRole

if TYPE_CHECKING:
    from ..context import RuntimeContext

# (intent_winner, chart_winner) → (role, priority)
# Priority: lower number = placed earlier in the dashboard (more prominent).
_ROLE_MAP: dict[tuple[str, str], tuple[str, int]] = {
    # KPI panels are always the executive summary
    ("kpi",          "kpi"):            ("resumen_ejecutivo",      1),
    # Trend is the primary narrative for most business dashboards
    ("trend",        "line"):           ("historia_principal",     2),
    ("trend",        "bar"):            ("historia_principal",     2),
    ("trend",        "bar_horizontal"): ("historia_principal",     2),
    # Comparison is the primary narrative when there is no trend
    ("comparison",   "bar"):            ("historia_principal",     2),
    ("comparison",   "bar_horizontal"): ("historia_principal",     2),
    # Ranking is secondary — provides context after the main story
    ("ranking",      "bar_horizontal"): ("explicacion_secundaria", 3),
    ("ranking",      "bar"):            ("explicacion_secundaria", 3),
    # Composition goes in secondary as well
    ("composition",  "pie"):            ("explicacion_secundaria", 3),
    ("composition",  "bar"):            ("explicacion_secundaria", 3),
    # Distribution and correlation are diagnostic — they explain WHY
    ("distribution", "histogram"):      ("diagnostico",            4),
    ("correlation",  "scatter"):        ("diagnostico",            4),
    ("anomaly",      "line"):           ("diagnostico",            4),
    ("anomaly",      "scatter"):        ("diagnostico",            4),
    # Cohort / retention are also diagnostic
    ("cohort",       "line"):           ("diagnostico",            4),
    ("retention",    "line"):           ("diagnostico",            4),
    # Detail views always go last
    ("detail",       "table"):          ("tabla_de_detalle",       5),
    # Funnel is secondary
    ("funnel",       "bar"):            ("explicacion_secundaria", 3),
    ("funnel",       "bar_horizontal"): ("explicacion_secundaria", 3),
}

# Fallback by intent only (when chart is not in the map)
_INTENT_FALLBACK: dict[str, tuple[str, int]] = {
    "kpi":          ("resumen_ejecutivo",      1),
    "trend":        ("historia_principal",     2),
    "comparison":   ("historia_principal",     2),
    "ranking":      ("explicacion_secundaria", 3),
    "composition":  ("explicacion_secundaria", 3),
    "distribution": ("diagnostico",            4),
    "correlation":  ("diagnostico",            4),
    "anomaly":      ("diagnostico",            4),
    "cohort":       ("diagnostico",            4),
    "retention":    ("diagnostico",            4),
    "funnel":       ("explicacion_secundaria", 3),
    "detail":       ("tabla_de_detalle",       5),
}


class DashboardRoleClassifier:
    """
    Assigns a narrative role to each panel based on (intent, chart_type).

    The role determines where the panel appears in the dashboard layout:
    resumen_ejecutivo → historia_principal → explicacion_secundaria →
    diagnostico → tabla_de_detalle → control

    DashboardLayoutOptimizer uses role.priority to order panels before packing.
    """

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.dashboard_role = self._classify(context)
        except Exception as e:
            context.errors.append(f"DashboardRoleClassifier: {e}")
        return context

    def _classify(self, context: RuntimeContext) -> DashboardRole:
        panel_id = getattr(context, "panel_id", "")
        intent = context.intent_winner
        chart = context.chart_winner

        role, priority = _ROLE_MAP.get(
            (intent, chart),
            _INTENT_FALLBACK.get(intent, ("historia_principal", 2)),
        )
        return DashboardRole(panel_id=panel_id, role=role, priority=priority)
