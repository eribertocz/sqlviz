from __future__ import annotations

from ..contracts.layout import (
    DashboardPlan,
    DashboardRole,
    LayoutDeclaration,
    PanelPlacement,
)

_GRID_WIDTH = 12


def _role_order(role: str) -> int:
    """Lower = placed earlier in the dashboard."""
    return {
        "resumen_ejecutivo":      1,
        "historia_principal":     2,
        "explicacion_secundaria": 3,
        "diagnostico":            4,
        "tabla_de_detalle":       5,
        "control":                6,
    }.get(role, 9)


class DashboardLayoutOptimizer:
    """
    Places all panels jointly onto a 12-column grid.

    Algorithm (GraphScape-inspired breadth-first row packing):
    1. Sort panels by DashboardRole.priority (KPIs first, detail last).
    2. Pack panels greedily into rows using col_span_preferred; fall back
       to col_span_min when preferred does not fit.
    3. resumen_ejecutivo (KPI) panels are always placed in their own
       dedicated row(s) at the top — they never share a row with
       historia_principal or lower roles.
    4. Full-width declarations (col_span_min == col_span_max == 12) always
       get their own row.

    This replaces the sequential packing in DashboardEngine V0.1.
    """

    def optimize(
        self,
        panels: list[tuple[LayoutDeclaration, DashboardRole]],
    ) -> DashboardPlan:
        if not panels:
            return DashboardPlan(placements=[], total_rows=0, utility_score=0.0)

        # Sort by role priority, then by panel_id for determinism
        sorted_panels = sorted(
            panels,
            key=lambda item: (item[1].priority, item[0].panel_id),
        )

        placements: list[PanelPlacement] = []
        current_row = 0
        current_col = 0
        current_row_role_group: str | None = None  # track the role group of current row

        for decl, role in sorted_panels:
            role_group = self._role_group(role.role)

            pref = decl.col_span_preferred
            mn = decl.col_span_min
            h = decl.height_px_preferred

            full_width = (mn == 12 or pref == 12 or decl.col_span_max == 12 and mn >= 10)

            # Force new row when:
            # (a) role group changes from resumen_ejecutivo to anything else
            # (b) full-width panel
            # (c) panel doesn't fit even with col_span_min
            if (
                current_col > 0
                and (
                    full_width
                    or mn > _GRID_WIDTH - current_col
                    or (current_row_role_group == "kpi" and role_group != "kpi")
                )
            ):
                current_row += 1
                current_col = 0

            # Decide actual col_span
            remaining = _GRID_WIDTH - current_col
            if full_width or pref > remaining:
                # Try to fit with preferred; if not, use min
                actual_span = pref if pref <= remaining else mn
                if actual_span > remaining:
                    # Needs its own row
                    if current_col > 0:
                        current_row += 1
                        current_col = 0
                    actual_span = min(pref, _GRID_WIDTH)
            else:
                actual_span = pref

            placements.append(
                PanelPlacement(
                    panel_id=decl.panel_id,
                    row=current_row,
                    col_offset=current_col,
                    col_span=actual_span,
                    height_px=h,
                )
            )

            current_col += actual_span
            current_row_role_group = role_group

            if current_col >= _GRID_WIDTH:
                current_row += 1
                current_col = 0
                current_row_role_group = None

        total_rows = (
            max((p.row for p in placements), default=-1) + 1
            if placements
            else 0
        )
        return DashboardPlan(
            placements=placements,
            total_rows=total_rows,
            utility_score=0.0,  # filled by DashboardObjective
        )

    @staticmethod
    def _role_group(role: str) -> str:
        return "kpi" if role == "resumen_ejecutivo" else "other"
