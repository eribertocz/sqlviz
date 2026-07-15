"""Tests for DashboardRoleClassifier — V0.2 Fase D.

≥ 2 positive (role fires as expected) + ≥ 2 negative per concept.
"""
from __future__ import annotations

from sqlviz_inference.context import ChartCandidate, RuntimeContext
from sqlviz_inference.layout.dashboard_role_classifier import DashboardRoleClassifier

clf = DashboardRoleClassifier()


def _ctx(intent: str, chart: str) -> RuntimeContext:
    return RuntimeContext(
        sql="SELECT x FROM t",
        chart_candidates=[
            ChartCandidate(
                chart_type=chart, affinity_score=1.0, penalty_total=0.0,
                final_score=1.0, normalized_score=1.0,
            )
        ],
        chart_winner=chart,
        intent_winner=intent,
    )


class TestKpiRole:

    def test_kpi_intent_kpi_chart_is_resumen_ejecutivo(self) -> None:
        ctx = _ctx("kpi", "kpi")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "resumen_ejecutivo"

    def test_kpi_has_priority_1(self) -> None:
        ctx = _ctx("kpi", "kpi")
        out = clf.run(ctx)
        assert out.dashboard_role.priority == 1

    def test_non_kpi_intent_is_not_resumen_ejecutivo(self) -> None:
        ctx = _ctx("trend", "line")
        out = clf.run(ctx)
        assert out.dashboard_role.role != "resumen_ejecutivo"

    def test_comparison_is_not_resumen_ejecutivo(self) -> None:
        ctx = _ctx("comparison", "bar")
        out = clf.run(ctx)
        assert out.dashboard_role.role != "resumen_ejecutivo"


class TestHistoriaPrincipal:

    def test_trend_line_is_historia_principal(self) -> None:
        ctx = _ctx("trend", "line")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "historia_principal"

    def test_comparison_bar_is_historia_principal(self) -> None:
        ctx = _ctx("comparison", "bar")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "historia_principal"

    def test_historia_principal_has_priority_2(self) -> None:
        ctx = _ctx("trend", "line")
        out = clf.run(ctx)
        assert out.dashboard_role.priority == 2

    def test_ranking_is_not_historia_principal(self) -> None:
        ctx = _ctx("ranking", "bar_horizontal")
        out = clf.run(ctx)
        assert out.dashboard_role.role != "historia_principal"


class TestExplicacionSecundaria:

    def test_ranking_bar_horizontal_is_explicacion_secundaria(self) -> None:
        ctx = _ctx("ranking", "bar_horizontal")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "explicacion_secundaria"

    def test_composition_pie_is_explicacion_secundaria(self) -> None:
        ctx = _ctx("composition", "pie")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "explicacion_secundaria"

    def test_explicacion_secundaria_has_priority_3(self) -> None:
        ctx = _ctx("ranking", "bar_horizontal")
        out = clf.run(ctx)
        assert out.dashboard_role.priority == 3

    def test_funnel_is_explicacion_secundaria(self) -> None:
        ctx = _ctx("funnel", "bar")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "explicacion_secundaria"


class TestDiagnostico:

    def test_distribution_histogram_is_diagnostico(self) -> None:
        ctx = _ctx("distribution", "histogram")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "diagnostico"

    def test_correlation_scatter_is_diagnostico(self) -> None:
        ctx = _ctx("correlation", "scatter")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "diagnostico"

    def test_diagnostico_has_priority_4(self) -> None:
        ctx = _ctx("distribution", "histogram")
        out = clf.run(ctx)
        assert out.dashboard_role.priority == 4

    def test_kpi_is_not_diagnostico(self) -> None:
        ctx = _ctx("kpi", "kpi")
        out = clf.run(ctx)
        assert out.dashboard_role.role != "diagnostico"


class TestTablaDeDetalle:

    def test_detail_table_is_tabla_de_detalle(self) -> None:
        ctx = _ctx("detail", "table")
        out = clf.run(ctx)
        assert out.dashboard_role.role == "tabla_de_detalle"

    def test_tabla_de_detalle_has_priority_5(self) -> None:
        ctx = _ctx("detail", "table")
        out = clf.run(ctx)
        assert out.dashboard_role.priority == 5

    def test_trend_is_not_tabla_de_detalle(self) -> None:
        ctx = _ctx("trend", "line")
        out = clf.run(ctx)
        assert out.dashboard_role.role != "tabla_de_detalle"

    def test_comparison_is_not_tabla_de_detalle(self) -> None:
        ctx = _ctx("comparison", "bar")
        out = clf.run(ctx)
        assert out.dashboard_role.role != "tabla_de_detalle"


class TestPriorityOrdering:

    def test_kpi_lower_priority_number_than_trend(self) -> None:
        kpi = clf.run(_ctx("kpi", "kpi")).dashboard_role.priority
        trend = clf.run(_ctx("trend", "line")).dashboard_role.priority
        assert kpi < trend

    def test_trend_lower_priority_number_than_ranking(self) -> None:
        trend = clf.run(_ctx("trend", "line")).dashboard_role.priority
        rank = clf.run(_ctx("ranking", "bar_horizontal")).dashboard_role.priority
        assert trend < rank

    def test_ranking_lower_priority_number_than_detail(self) -> None:
        rank = clf.run(_ctx("ranking", "bar_horizontal")).dashboard_role.priority
        detail = clf.run(_ctx("detail", "table")).dashboard_role.priority
        assert rank < detail

    def test_role_written_to_context(self) -> None:
        ctx = _ctx("kpi", "kpi")
        out = clf.run(ctx)
        assert out.dashboard_role is not None
