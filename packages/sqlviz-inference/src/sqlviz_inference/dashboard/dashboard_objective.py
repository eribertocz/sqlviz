from __future__ import annotations

from ..contracts.layout import DashboardPlan, DashboardRole, LayoutDeclaration

_GRID_WIDTH = 12

# Weights for the 10-dimension objective (positive − negative)
_W_POS = {
    "comprehension":         0.25,
    "semantic_fidelity":     0.20,
    "readability":           0.15,
    "narrative_coherence":   0.15,
    "information_coverage":  0.10,
    "business_priority":     0.15,
}
_W_NEG = {
    "cognitive_load":        0.10,
    "clutter":               0.05,
    "redundancy":            0.05,
    "wasted_space":          0.05,
}


class DashboardObjective:
    """
    Evaluates a DashboardPlan holistically — not just whether individual panels
    are good, but whether the DASHBOARD as a whole is coherent and readable.

    utility_score ∈ [0, 1].  Score > 0.5 means the plan is acceptable.

    Dimensions:
      Positive: comprehension, semantic_fidelity, readability,
                narrative_coherence, information_coverage, business_priority
      Negative: cognitive_load, clutter, redundancy, wasted_space
    """

    def score(
        self,
        plan: DashboardPlan,
        declarations: list[LayoutDeclaration],
        roles: list[DashboardRole],
        redundancy_count: int = 0,
    ) -> float:
        if not plan.placements:
            return 0.0

        decl_map = {d.panel_id: d for d in declarations}
        role_map = {r.panel_id: r for r in roles}

        # ── Positive dimensions ────────────────────────────────────────────

        comprehension = self._comprehension(plan, role_map)
        semantic_fidelity = self._semantic_fidelity(role_map)
        readability = self._readability(plan, decl_map)
        narrative_coherence = self._narrative_coherence(plan, role_map)
        information_coverage = self._information_coverage(role_map)
        business_priority = self._business_priority(plan, role_map)

        pos = (
            _W_POS["comprehension"]       * comprehension
            + _W_POS["semantic_fidelity"] * semantic_fidelity
            + _W_POS["readability"]       * readability
            + _W_POS["narrative_coherence"] * narrative_coherence
            + _W_POS["information_coverage"] * information_coverage
            + _W_POS["business_priority"] * business_priority
        )

        # ── Negative dimensions ────────────────────────────────────────────

        cognitive_load = self._cognitive_load(plan, role_map)
        clutter = self._clutter(plan)
        redundancy = min(1.0, redundancy_count / max(1, len(plan.placements)))
        wasted_space = self._wasted_space(plan)

        neg = (
            _W_NEG["cognitive_load"] * cognitive_load
            + _W_NEG["clutter"]      * clutter
            + _W_NEG["redundancy"]   * redundancy
            + _W_NEG["wasted_space"] * wasted_space
        )

        return round(max(0.0, min(1.0, pos - neg)), 4)

    # ── Positive dimension scorers ─────────────────────────────────────────

    def _comprehension(
        self, plan: DashboardPlan, role_map: dict[str, DashboardRole]
    ) -> float:
        # KPIs in row 0, narrative panels follow in correct order
        if not plan.placements:
            return 0.0
        kpi_rows = {
            p.row for p in plan.placements
            if role_map.get(p.panel_id, DashboardRole("", priority=9)).role
            == "resumen_ejecutivo"
        }
        other_rows = {
            p.row for p in plan.placements
            if role_map.get(p.panel_id, DashboardRole("", priority=9)).role
            != "resumen_ejecutivo"
        }
        if not kpi_rows:
            return 0.70  # no KPIs — comprehension still possible
        max_kpi_row = max(kpi_rows)
        if other_rows and min(other_rows) > max_kpi_row:
            return 1.0  # KPIs before all other panels
        return 0.50

    def _semantic_fidelity(self, role_map: dict[str, DashboardRole]) -> float:
        if not role_map:
            return 0.50
        known = sum(
            1 for r in role_map.values()
            if r.role != "historia_principal"  # not the generic fallback
        )
        return 0.60 + 0.40 * (known / len(role_map))

    def _readability(
        self, plan: DashboardPlan, decl_map: dict[str, LayoutDeclaration]
    ) -> float:
        if not plan.placements:
            return 0.50
        scores = []
        for p in plan.placements:
            d = decl_map.get(p.panel_id)
            if d is None:
                scores.append(0.70)
                continue
            # Preferred width respected?
            if d.col_span_min <= p.col_span <= d.col_span_max:
                scores.append(1.0)
            elif p.col_span < d.col_span_min:
                scores.append(0.50)  # too narrow
            else:
                scores.append(0.80)  # slightly wider than declared max — still ok
            # Height within bounds?
            if d.height_px_min <= p.height_px <= d.height_px_max:
                scores[-1] = min(1.0, scores[-1])
            else:
                scores[-1] = max(0.0, scores[-1] - 0.10)
        return sum(scores) / len(scores)

    def _narrative_coherence(
        self, plan: DashboardPlan, role_map: dict[str, DashboardRole]
    ) -> float:
        if not plan.placements:
            return 0.50
        # Check that panels within a row have similar or adjacent priorities
        rows: dict[int, list[str]] = {}
        for p in plan.placements:
            rows.setdefault(p.row, []).append(p.panel_id)

        row_coherences = []
        for row_ids in rows.values():
            priorities = [
                role_map.get(pid, DashboardRole("", priority=5)).priority
                for pid in row_ids
            ]
            spread = max(priorities) - min(priorities)
            row_coherences.append(1.0 if spread <= 1 else max(0.0, 1.0 - spread * 0.2))

        return sum(row_coherences) / len(row_coherences)

    def _information_coverage(self, role_map: dict[str, DashboardRole]) -> float:
        roles_present = {r.role for r in role_map.values()}
        # A comprehensive dashboard covers summary + narrative + detail
        coverage_roles = {"resumen_ejecutivo", "historia_principal", "tabla_de_detalle"}
        covered = coverage_roles & roles_present
        return len(covered) / len(coverage_roles)

    def _business_priority(
        self, plan: DashboardPlan, role_map: dict[str, DashboardRole]
    ) -> float:
        # High-priority panels (priority ≤ 2) should appear in earlier rows
        if not plan.placements:
            return 0.50
        high_priority_rows = [
            p.row for p in plan.placements
            if role_map.get(p.panel_id, DashboardRole("", priority=9)).priority <= 2
        ]
        if not high_priority_rows:
            return 0.60
        avg_row = sum(high_priority_rows) / len(high_priority_rows)
        # Perfect = avg row is 0; penalize if high-priority panels are deep
        return max(0.0, 1.0 - avg_row * 0.15)

    # ── Negative dimension scorers ─────────────────────────────────────────

    def _cognitive_load(
        self, plan: DashboardPlan, role_map: dict[str, DashboardRole]
    ) -> float:
        n = len(plan.placements)
        if n <= 4:
            return 0.10
        if n <= 7:
            return 0.30
        return min(0.80, 0.30 + (n - 7) * 0.05)

    def _clutter(self, plan: DashboardPlan) -> float:
        if not plan.placements:
            return 0.0
        # Many panels per row = more clutter
        rows: dict[int, int] = {}
        for p in plan.placements:
            rows[p.row] = rows.get(p.row, 0) + 1
        max_per_row = max(rows.values(), default=1)
        return min(0.80, max(0.0, (max_per_row - 3) * 0.15))

    def _wasted_space(self, plan: DashboardPlan) -> float:
        if not plan.placements or plan.total_rows == 0:
            return 0.0
        # Fraction of grid cells unused across all rows
        cells_used = sum(p.col_span for p in plan.placements)
        cells_total = plan.total_rows * _GRID_WIDTH
        used_fraction = cells_used / cells_total
        return max(0.0, 1.0 - used_fraction)
