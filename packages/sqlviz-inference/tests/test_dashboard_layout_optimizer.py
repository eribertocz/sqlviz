"""Tests for DashboardLayoutOptimizer — V0.2 Fase D."""
from __future__ import annotations

import pytest

from sqlviz_inference.contracts.layout import DashboardRole, LayoutDeclaration
from sqlviz_inference.dashboard.dashboard_layout_optimizer import DashboardLayoutOptimizer

optimizer = DashboardLayoutOptimizer()


def _decl(
    panel_id: str,
    col_min: int = 4,
    col_pref: int = 6,
    col_max: int = 12,
    height: int = 360,
) -> LayoutDeclaration:
    return LayoutDeclaration(
        panel_id=panel_id,
        col_span_min=col_min,
        col_span_preferred=col_pref,
        col_span_max=col_max,
        height_px_min=int(height * 0.7),
        height_px_preferred=height,
        height_px_max=int(height * 1.4),
    )


def _role(panel_id: str, role: str, priority: int) -> DashboardRole:
    return DashboardRole(panel_id=panel_id, role=role, priority=priority)


def _kpi(pid: str) -> tuple[LayoutDeclaration, DashboardRole]:
    return _decl(pid, 3, 3, 4, 180), _role(pid, "resumen_ejecutivo", 1)


def _line(pid: str) -> tuple[LayoutDeclaration, DashboardRole]:
    return _decl(pid, 8, 12, 12, 360), _role(pid, "historia_principal", 2)


def _bar(pid: str) -> tuple[LayoutDeclaration, DashboardRole]:
    return _decl(pid, 6, 12, 12, 300), _role(pid, "historia_principal", 2)


def _bar_h(pid: str) -> tuple[LayoutDeclaration, DashboardRole]:
    return _decl(pid, 6, 8, 12, 320), _role(pid, "explicacion_secundaria", 3)


def _hist(pid: str) -> tuple[LayoutDeclaration, DashboardRole]:
    return _decl(pid, 4, 6, 10, 300), _role(pid, "diagnostico", 4)


def _table(pid: str) -> tuple[LayoutDeclaration, DashboardRole]:
    return _decl(pid, 8, 12, 12, 360), _role(pid, "tabla_de_detalle", 5)


class TestEmptyAndSingle:

    def test_empty_produces_empty_plan(self) -> None:
        plan = optimizer.optimize([])
        assert plan.placements == []
        assert plan.total_rows == 0

    def test_single_panel_placed_at_row_0(self) -> None:
        plan = optimizer.optimize([_kpi("p1")])
        assert len(plan.placements) == 1
        assert plan.placements[0].row == 0

    def test_single_panel_uses_preferred_span(self) -> None:
        plan = optimizer.optimize([_line("p1")])
        p = plan.placements[0]
        assert p.col_span == 12


class TestKpiFirst:

    def test_kpi_placed_before_other_panels(self) -> None:
        # 1 KPI + 1 line; KPI should be in a lower row index than line
        plan = optimizer.optimize([_line("p_line"), _kpi("p_kpi")])
        kpi_row = next(p.row for p in plan.placements if p.panel_id == "p_kpi")
        line_row = next(p.row for p in plan.placements if p.panel_id == "p_line")
        assert kpi_row <= line_row

    def test_two_kpis_placed_in_same_row(self) -> None:
        plan = optimizer.optimize([_kpi("k1"), _kpi("k2")])
        rows = {p.row for p in plan.placements}
        # Two KPIs with col_span_preferred=3 should fit in one row (3+3=6 ≤ 12)
        assert len(rows) == 1

    def test_kpis_separate_from_narrative_panels(self) -> None:
        panels = [_kpi("k1"), _kpi("k2"), _line("p_line")]
        plan = optimizer.optimize(panels)
        kpi_rows = {p.row for p in plan.placements if p.panel_id in ("k1", "k2")}
        line_row = next(p.row for p in plan.placements if p.panel_id == "p_line")
        assert all(r < line_row for r in kpi_rows)

    def test_4_kpis_fit_in_first_row(self) -> None:
        panels = [_kpi(f"k{i}") for i in range(4)]
        plan = optimizer.optimize(panels)
        rows = {p.row for p in plan.placements}
        # 4 × col_span_preferred=3 = 12 — exactly one row
        assert len(rows) == 1


class TestRowPacking:

    def test_panels_pack_into_rows_up_to_12(self) -> None:
        # Two bar_horizontal with col_span_preferred=8 cannot share a row (8+8=16>12)
        panels = [_bar_h("bh1"), _bar_h("bh2")]
        plan = optimizer.optimize(panels)
        rows = {p.row for p in plan.placements}
        assert len(rows) == 2

    def test_panels_that_fit_share_a_row(self) -> None:
        # Two hist with col_span_preferred=6 fit (6+6=12)
        panels = [_hist("h1"), _hist("h2")]
        plan = optimizer.optimize(panels)
        rows = {p.row for p in plan.placements}
        assert len(rows) == 1

    def test_full_width_panel_gets_own_row(self) -> None:
        # line has col_span_preferred=12 (full width)
        panels = [_line("p1"), _hist("h1"), _hist("h2")]
        plan = optimizer.optimize(panels)
        line_row = next(p.row for p in plan.placements if p.panel_id == "p1")
        hist_rows = [p.row for p in plan.placements if p.panel_id in ("h1", "h2")]
        # Line is full-width and should not share its row with histograms
        assert all(r != line_row for r in hist_rows)

    def test_all_panels_placed(self) -> None:
        panels = [_kpi("k"), _line("l"), _bar("b"), _bar_h("bh"), _table("t")]
        plan = optimizer.optimize(panels)
        assert len(plan.placements) == 5

    def test_total_rows_correct(self) -> None:
        panels = [_kpi("k"), _line("l")]
        plan = optimizer.optimize(panels)
        assert plan.total_rows == plan.placements[-1].row + 1 if plan.placements else 0


class TestNarrativeOrder:

    def test_historia_principal_before_explicacion_secundaria(self) -> None:
        panels = [_bar_h("bh"), _line("l")]  # bh=explicacion_sec, line=historia
        plan = optimizer.optimize(panels)
        line_row = next(p.row for p in plan.placements if p.panel_id == "l")
        bh_row = next(p.row for p in plan.placements if p.panel_id == "bh")
        assert line_row <= bh_row

    def test_tabla_de_detalle_last(self) -> None:
        panels = [_table("t"), _kpi("k"), _line("l")]
        plan = optimizer.optimize(panels)
        table_row = next(p.row for p in plan.placements if p.panel_id == "t")
        other_rows = [p.row for p in plan.placements if p.panel_id != "t"]
        assert table_row >= max(other_rows)

    def test_6_panel_dashboard_kpis_in_row_0(self) -> None:
        panels = [_kpi("k1"), _kpi("k2"), _line("l"), _bar("b"), _hist("h"), _table("t")]
        plan = optimizer.optimize(panels)
        kpi_rows = {p.row for p in plan.placements if p.panel_id in ("k1", "k2")}
        assert kpi_rows == {0}
