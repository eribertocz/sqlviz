"""Tests for DashboardObjective — V0.2 Fase D."""
from __future__ import annotations

import pytest

from sqlviz_inference.contracts.layout import (
    DashboardPlan,
    DashboardRole,
    LayoutDeclaration,
    PanelPlacement,
)
from sqlviz_inference.dashboard.dashboard_objective import DashboardObjective

objective = DashboardObjective()


def _plan(*placements: PanelPlacement) -> DashboardPlan:
    total = max((p.row for p in placements), default=-1) + 1 if placements else 0
    return DashboardPlan(placements=list(placements), total_rows=total)


def _placement(pid: str, row: int, col: int, span: int, h: int = 360) -> PanelPlacement:
    return PanelPlacement(panel_id=pid, row=row, col_offset=col, col_span=span, height_px=h)


def _role(pid: str, role: str, priority: int) -> DashboardRole:
    return DashboardRole(panel_id=pid, role=role, priority=priority)


def _decl(pid: str, col_min=4, col_pref=6, col_max=12, h_pref=360) -> LayoutDeclaration:
    return LayoutDeclaration(
        panel_id=pid,
        col_span_min=col_min,
        col_span_preferred=col_pref,
        col_span_max=col_max,
        height_px_min=int(h_pref * 0.7),
        height_px_preferred=h_pref,
        height_px_max=int(h_pref * 1.4),
    )


class TestUtilityScorePositive:

    def test_empty_plan_returns_zero(self) -> None:
        plan = DashboardPlan(placements=[], total_rows=0)
        score = objective.score(plan, [], [])
        assert score == 0.0

    def test_simple_plan_produces_positive_score(self) -> None:
        plan = _plan(_placement("k", 0, 0, 4, 180))
        decls = [_decl("k", 2, 3, 4, 180)]
        roles = [_role("k", "resumen_ejecutivo", 1)]
        score = objective.score(plan, decls, roles)
        assert score > 0.0

    def test_well_formed_dashboard_scores_above_half(self) -> None:
        # KPI + line + table — canonical well-formed dashboard
        plan = _plan(
            _placement("k", 0, 0, 3, 180),
            _placement("l", 1, 0, 12, 360),
            _placement("t", 2, 0, 12, 360),
        )
        decls = [
            _decl("k", 2, 3, 4, 180),
            _decl("l", 8, 12, 12, 360),
            _decl("t", 8, 12, 12, 360),
        ]
        roles = [
            _role("k", "resumen_ejecutivo", 1),
            _role("l", "historia_principal", 2),
            _role("t", "tabla_de_detalle", 5),
        ]
        score = objective.score(plan, decls, roles)
        assert score > 0.50

    def test_score_in_zero_one_range(self) -> None:
        plan = _plan(
            _placement("k", 0, 0, 3, 180),
            _placement("l", 1, 0, 12, 360),
        )
        score = objective.score(
            plan,
            [_decl("k"), _decl("l", 8, 12, 12)],
            [_role("k", "resumen_ejecutivo", 1), _role("l", "historia_principal", 2)],
        )
        assert 0.0 <= score <= 1.0


class TestUtilityScoreNegatives:

    def test_redundancy_lowers_score(self) -> None:
        plan = _plan(_placement("k", 0, 0, 3, 180), _placement("l", 1, 0, 12, 360))
        decls = [_decl("k"), _decl("l")]
        roles = [_role("k", "resumen_ejecutivo", 1), _role("l", "historia_principal", 2)]
        score_no_redundancy = objective.score(plan, decls, roles, redundancy_count=0)
        score_with_redundancy = objective.score(plan, decls, roles, redundancy_count=1)
        assert score_with_redundancy < score_no_redundancy

    def test_many_panels_increases_cognitive_load(self) -> None:
        # 8-panel dashboard should score lower due to cognitive_load penalty
        placements = [_placement(f"p{i}", i, 0, 6) for i in range(8)]
        plan = _plan(*placements)
        decls = [_decl(f"p{i}") for i in range(8)]
        roles = [_role(f"p{i}", "historia_principal", 2) for i in range(8)]
        score_large = objective.score(plan, decls, roles)

        placements2 = [_placement(f"q{i}", i, 0, 6) for i in range(3)]
        plan2 = _plan(*placements2)
        decls2 = [_decl(f"q{i}") for i in range(3)]
        roles2 = [_role(f"q{i}", "historia_principal", 2) for i in range(3)]
        score_small = objective.score(plan2, decls2, roles2)

        assert score_small > score_large

    def test_wasted_space_penalizes(self) -> None:
        # Panel occupying only 3 of 12 cols wastes 75% of a row
        plan = _plan(_placement("p", 0, 0, 3, 360))
        decls = [_decl("p", 3, 3, 3)]
        roles = [_role("p", "historia_principal", 2)]
        score = objective.score(plan, decls, roles)
        # Utility should be limited by the wasted_space penalty
        assert score < 0.80


class TestKpiOrdering:

    def test_kpis_first_improves_comprehension(self) -> None:
        # KPI in row 0, others in row 1 = good comprehension
        plan_good = _plan(
            _placement("k", 0, 0, 3, 180),
            _placement("l", 1, 0, 12, 360),
        )
        # KPI in row 1, line in row 0 = bad comprehension (KPI not first)
        plan_bad = _plan(
            _placement("l", 0, 0, 12, 360),
            _placement("k", 1, 0, 3, 180),
        )
        decls = [_decl("k", 2, 3, 4, 180), _decl("l", 8, 12, 12, 360)]
        roles = [_role("k", "resumen_ejecutivo", 1), _role("l", "historia_principal", 2)]
        score_good = objective.score(plan_good, decls, roles)
        score_bad = objective.score(plan_bad, decls, roles)
        assert score_good > score_bad
