"""Dashboard stress tests — Entrega 3.C (scenarios A, B, C, D, E).

Each scenario builds a realistic multi-panel dashboard and asserts:
  - No row exceeds 12 columns (100% width)
  - Full-width panels (col_span=12) never share a row
  - KPI panels always occupy the leading row(s)
  - Narrative ordering: trend → comparison → ranking → ... → detail
  - Detail panels always appear last
  - Scenario-specific structural invariants
"""

from __future__ import annotations

import random
from typing import ClassVar

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.dashboard.dashboard_engine import DashboardEngine, DashboardLayout
from sqlviz_inference.pipeline import RuntimePipeline
from sqlviz_inference.result import InferenceResult

# Type alias for panel definition tuples (avoids 100+ char type annotations)
_PanelDef = tuple[
    str,                             # panel_id
    str,                             # sql
    list[dict[str, object]] | None,  # data
    list[tuple[str, str]] | None,    # schema_defs
]

# ---------------------------------------------------------------------------
# Module-level pipeline singletons
# ---------------------------------------------------------------------------

_pipeline = RuntimePipeline()
_engine = DashboardEngine()


def _infer(
    sql: str,
    data: list[dict[str, object]] | None = None,
    schema_defs: list[tuple[str, str]] | None = None,
) -> InferenceResult:
    schema = [ColumnSchema(name=n, type=t) for n, t in (schema_defs or [])]
    ctx = RuntimeContext(sql=sql, data=data or [], schema=schema)
    ctx = _pipeline.run(ctx)
    return InferenceResult.from_context(ctx)


def _compose(
    panel_defs: list[_PanelDef],
) -> tuple[list[tuple[str, InferenceResult]], DashboardLayout]:
    results = [(pid, _infer(sql, data, schema)) for pid, sql, data, schema in panel_defs]
    return results, _engine.compose(results)


# ---------------------------------------------------------------------------
# Shared assertion helpers
# ---------------------------------------------------------------------------

def _assert_no_row_overflow(layout: DashboardLayout) -> None:
    for i, row in enumerate(layout.rows):
        assert row.total_span <= 12, (
            f"Row {i} exceeds 12 columns: total_span={row.total_span}, "
            f"panels={[(p.panel_id, p.final_col_span) for p in row.panels]}"
        )


def _assert_full_width_alone(layout: DashboardLayout) -> None:
    for i, row in enumerate(layout.rows):
        for panel in row.panels:
            if panel.final_col_span == 12:
                assert len(row.panels) == 1, (
                    f"Full-width panel '{panel.panel_id}' shares row {i} "
                    f"with: {[p.panel_id for p in row.panels if p.panel_id != panel.panel_id]}"
                )


def _assert_kpis_lead(layout: DashboardLayout) -> None:
    """All KPI panels appear in rows that precede any non-KPI row."""
    kpi_row_indices = {
        p.row_index
        for row in layout.rows
        for p in row.panels
        if p.inference_result.chart_winner == "kpi"
    }
    other_row_indices = {
        p.row_index
        for row in layout.rows
        for p in row.panels
        if p.inference_result.chart_winner != "kpi"
    }
    if kpi_row_indices and other_row_indices:
        assert max(kpi_row_indices) < min(other_row_indices), (
            f"KPI rows {sorted(kpi_row_indices)} overlap or come after "
            f"non-KPI rows {sorted(other_row_indices)}"
        )


def _assert_detail_last(layout: DashboardLayout) -> None:
    """Detail (table) panels appear only in the last row(s)."""
    detail_row_indices = {
        p.row_index
        for row in layout.rows
        for p in row.panels
        if p.inference_result.intent_winner == "detail"
    }
    non_detail_row_indices = {
        p.row_index
        for row in layout.rows
        for p in row.panels
        if p.inference_result.intent_winner != "detail"
    }
    if detail_row_indices and non_detail_row_indices:
        assert min(detail_row_indices) > max(non_detail_row_indices), (
            f"Detail rows {sorted(detail_row_indices)} appear before "
            f"non-detail rows {sorted(non_detail_row_indices)}"
        )


def _assert_intent_order_before(
    layout: DashboardLayout,
    earlier_intent: str,
    later_intent: str,
) -> None:
    """Panels with earlier_intent appear in strictly lower row indices than later_intent."""
    earlier_rows = {
        p.row_index
        for row in layout.rows
        for p in row.panels
        if p.inference_result.intent_winner == earlier_intent
    }
    later_rows = {
        p.row_index
        for row in layout.rows
        for p in row.panels
        if p.inference_result.intent_winner == later_intent
    }
    if earlier_rows and later_rows:
        assert max(earlier_rows) < min(later_rows), (
            f"{earlier_intent} rows {sorted(earlier_rows)} do not precede "
            f"{later_intent} rows {sorted(later_rows)}"
        )


# ---------------------------------------------------------------------------
# Shared data builders
# ---------------------------------------------------------------------------

def _monthly(n: int = 12, field: str = "total", base: int = 10000) -> list[dict[str, object]]:
    return [{"mes": f"2024-{i:02d}-01", field: base + i * 500} for i in range(1, n + 1)]


# ===========================================================================
# Scenario A — Executive Dashboard (15 panels)
# ===========================================================================

_EXEC_PANELS: list[_PanelDef] = [
    # 4 KPIs
    ("kpi_revenue",   "SELECT SUM(revenue) AS total FROM sales",
     [{"total": 1250000.0}], [("total", "DOUBLE")]),
    ("kpi_orders",    "SELECT COUNT(*) AS total_orders FROM orders",
     [{"total_orders": 4521}], [("total_orders", "BIGINT")]),
    ("kpi_customers", "SELECT COUNT(DISTINCT customer_id) AS clientes FROM orders",
     [{"clientes": 892}], [("clientes", "BIGINT")]),
    ("kpi_nps",       "SELECT AVG(nps_score) AS nps FROM surveys",
     [{"nps": 42.0}], [("nps", "DOUBLE")]),
    # 4 Trends
    ("trend_revenue",
     "SELECT mes, SUM(revenue) AS total FROM sales GROUP BY mes ORDER BY mes",
     _monthly(12, "total", 80000), [("mes", "DATE"), ("revenue", "DOUBLE")]),
    ("trend_orders",
     "SELECT mes, COUNT(*) AS pedidos FROM orders GROUP BY mes ORDER BY mes",
     _monthly(12, "pedidos", 300), [("mes", "DATE"), ("pedidos", "BIGINT")]),
    ("trend_mau",
     "SELECT mes, COUNT(DISTINCT user_id) AS usuarios FROM events "
     "GROUP BY mes ORDER BY mes",
     _monthly(12, "usuarios", 5000), [("mes", "DATE"), ("usuarios", "BIGINT")]),
    ("trend_mrr",
     "SELECT mes, SUM(mrr) AS mrr FROM subscriptions GROUP BY mes ORDER BY mes",
     _monthly(12, "mrr", 12000), [("mes", "DATE"), ("mrr", "DOUBLE")]),
    # 3 Comparisons (5 categories → comparison, not composition)
    ("comp_region",
     "SELECT region, SUM(revenue) AS total FROM sales GROUP BY region",
     [{"region": r, "total": v} for r, v in
      [("Norte", 45000), ("Sur", 32000), ("Este", 28000), ("Oeste", 19000), ("Centro", 22000)]],
     [("region", "VARCHAR"), ("revenue", "DOUBLE")]),
    ("comp_product",
     "SELECT producto, SUM(revenue) AS total FROM sales GROUP BY producto",
     [{"producto": p, "total": v} for p, v in
      [("A", 80000), ("B", 65000), ("C", 45000), ("D", 30000), ("E", 20000)]],
     [("producto", "VARCHAR"), ("revenue", "DOUBLE")]),
    ("comp_canal",
     "SELECT canal, SUM(revenue) AS total FROM sales GROUP BY canal",
     [{"canal": c, "total": v} for c, v in
      [("Online", 70000), ("Tienda", 55000), ("Tel", 25000), ("Partner", 15000), ("Otro", 8000)]],
     [("canal", "VARCHAR"), ("revenue", "DOUBLE")]),
    # 2 Rankings
    ("ranking_clients",
     "SELECT cliente, SUM(revenue) AS total FROM sales "
     "GROUP BY cliente ORDER BY total DESC LIMIT 10",
     [{"cliente": f"C{i}", "total": (10 - i) * 50000.0} for i in range(10)],
     [("cliente", "VARCHAR"), ("revenue", "DOUBLE")]),
    ("ranking_products",
     "SELECT producto, SUM(unidades) AS total FROM sales "
     "GROUP BY producto ORDER BY total DESC LIMIT 10",
     [{"producto": f"P{i}", "total": (10 - i) * 1000.0} for i in range(10)],
     [("producto", "VARCHAR"), ("unidades", "BIGINT")]),
    # 2 Detail tables
    ("detail_trans",
     "SELECT id, fecha, cliente, producto, monto, estado FROM transacciones",
     None, [("id", "BIGINT"), ("fecha", "DATE"), ("cliente", "VARCHAR"),
            ("producto", "VARCHAR"), ("monto", "DOUBLE"), ("estado", "VARCHAR")]),
    ("detail_clients",
     "SELECT id, nombre, email, region, segmento, fecha_alta FROM clientes",
     None, [("id", "BIGINT"), ("nombre", "VARCHAR"), ("email", "VARCHAR"),
            ("region", "VARCHAR"), ("segmento", "VARCHAR"), ("fecha_alta", "DATE")]),
]


class TestDashboardExecutive:
    """Scenario A: 15-panel executive dashboard."""

    _results: ClassVar[list[tuple[str, InferenceResult]]]
    _layout: ClassVar[DashboardLayout]

    @classmethod
    def setup_class(cls) -> None:
        cls._results, cls._layout = _compose(_EXEC_PANELS)

    def test_all_panels_inferred(self) -> None:
        assert len(self._results) == 15

    def test_kpi_panels_are_kpi(self) -> None:
        kpi_ids = {"kpi_revenue", "kpi_orders", "kpi_customers", "kpi_nps"}
        for pid, r in self._results:
            if pid in kpi_ids:
                assert r.chart_winner == "kpi", f"{pid}: expected kpi, got {r.chart_winner}"

    def test_trend_panels_are_line(self) -> None:
        trend_ids = {"trend_revenue", "trend_orders", "trend_mau", "trend_mrr"}
        for pid, r in self._results:
            if pid in trend_ids:
                assert r.chart_winner == "line", f"{pid}: expected line, got {r.chart_winner}"

    def test_no_row_overflow(self) -> None:
        _assert_no_row_overflow(self._layout)

    def test_full_width_panels_alone(self) -> None:
        _assert_full_width_alone(self._layout)

    def test_kpis_lead(self) -> None:
        _assert_kpis_lead(self._layout)

    def test_kpis_in_single_row(self) -> None:
        """4 KPIs → exactly 1 row, each col_span=3, total=12."""
        kpi_rows = [
            row for row in self._layout.rows
            if all(p.inference_result.chart_winner == "kpi" for p in row.panels)
        ]
        assert len(kpi_rows) == 1
        kpi_row = kpi_rows[0]
        assert len(kpi_row.panels) == 4
        assert kpi_row.total_span == 12
        assert all(p.final_col_span == 3 for p in kpi_row.panels)

    def test_trends_before_detail(self) -> None:
        _assert_intent_order_before(self._layout, "trend", "detail")

    def test_comparisons_before_detail(self) -> None:
        _assert_intent_order_before(self._layout, "comparison", "detail")

    def test_rankings_before_detail(self) -> None:
        _assert_intent_order_before(self._layout, "ranking", "detail")

    def test_detail_last(self) -> None:
        _assert_detail_last(self._layout)

    def test_narrative_order_trend_before_comparison(self) -> None:
        _assert_intent_order_before(self._layout, "trend", "comparison")

    def test_narrative_order_comparison_before_ranking(self) -> None:
        _assert_intent_order_before(self._layout, "comparison", "ranking")


# ===========================================================================
# Scenario B — Commercial Billing Dashboard (8 panels)
# ===========================================================================

_BILLING_PANELS: list[_PanelDef] = [
    ("kpi_recuperacion",
     "SELECT SUM(cobrado) / SUM(facturado) AS recuperacion FROM cobranza",
     [{"recuperacion": 0.87}], [("recuperacion", "DOUBLE")]),
    ("kpi_deuda_vencida",
     "SELECT SUM(monto) AS deuda_vencida FROM cartera",
     [{"deuda_vencida": 125000.0}], [("deuda_vencida", "DOUBLE")]),
    ("trend_facturacion",
     "SELECT mes, SUM(monto) AS facturado FROM facturacion GROUP BY mes ORDER BY mes",
     _monthly(12, "facturado", 90000), [("mes", "DATE"), ("monto", "DOUBLE")]),
    ("trend_cobranza",
     "SELECT mes, SUM(cobrado) AS cobranza FROM cobranza GROUP BY mes ORDER BY mes",
     _monthly(12, "cobranza", 78000), [("mes", "DATE"), ("cobrado", "DOUBLE")]),
    ("ranking_deudores",
     "SELECT cliente, SUM(deuda) AS deuda FROM cartera "
     "GROUP BY cliente ORDER BY deuda DESC LIMIT 10",
     [{"cliente": f"C{i}", "deuda": (10 - i) * 15000.0} for i in range(10)],
     [("cliente", "VARCHAR"), ("deuda", "DOUBLE")]),
    ("comp_categoria",
     "SELECT categoria, SUM(facturado) AS total FROM facturacion GROUP BY categoria",
     [{"categoria": c, "total": v} for c, v in
      [("A", 200000), ("B", 150000), ("C", 100000), ("D", 75000), ("E", 50000)]],
     [("categoria", "VARCHAR"), ("facturado", "DOUBLE")]),
    ("comp_area",
     "SELECT area, SUM(facturado) AS total FROM facturacion GROUP BY area",
     [{"area": a, "total": v} for a, v in
      [("Norte", 180000), ("Sur", 140000), ("Este", 110000), ("Oeste", 90000), ("Centro", 120000)]],
     [("area", "VARCHAR"), ("facturado", "DOUBLE")]),
    ("detail_facturas",
     "SELECT id, cliente, categoria, area, fecha, monto FROM facturas",
     None, [("id", "BIGINT"), ("cliente", "VARCHAR"), ("categoria", "VARCHAR"),
            ("area", "VARCHAR"), ("fecha", "DATE"), ("monto", "DOUBLE")]),
]


class TestDashboardBilling:
    """Scenario B: 8-panel commercial billing dashboard."""

    _results: ClassVar[list[tuple[str, InferenceResult]]]
    _layout: ClassVar[DashboardLayout]

    @classmethod
    def setup_class(cls) -> None:
        cls._results, cls._layout = _compose(_BILLING_PANELS)

    def test_all_panels_inferred(self) -> None:
        assert len(self._results) == 8

    def test_kpis_are_kpi(self) -> None:
        for pid, r in self._results:
            if pid.startswith("kpi_"):
                assert r.chart_winner == "kpi", f"{pid}: expected kpi, got {r.chart_winner}"

    def test_trends_are_line(self) -> None:
        for pid, r in self._results:
            if pid.startswith("trend_"):
                assert r.chart_winner == "line", f"{pid}: expected line, got {r.chart_winner}"

    def test_no_row_overflow(self) -> None:
        _assert_no_row_overflow(self._layout)

    def test_full_width_panels_alone(self) -> None:
        _assert_full_width_alone(self._layout)

    def test_kpis_lead(self) -> None:
        _assert_kpis_lead(self._layout)

    def test_kpi_row_has_two_kpis(self) -> None:
        """2 KPIs → 1 row, span=4 each (KPI Shelf v0.1), total=8, offset=2 on first."""
        kpi_rows = [
            row for row in self._layout.rows
            if all(p.inference_result.chart_winner == "kpi" for p in row.panels)
        ]
        assert len(kpi_rows) == 1
        assert len(kpi_rows[0].panels) == 2
        assert all(p.final_col_span == 4 for p in kpi_rows[0].panels)
        assert kpi_rows[0].total_span == 8
        assert kpi_rows[0].panels[0].col_offset == 2
        assert kpi_rows[0].panels[1].col_offset == 0

    def test_trends_before_comparisons(self) -> None:
        _assert_intent_order_before(self._layout, "trend", "comparison")

    def test_comparisons_before_ranking(self) -> None:
        _assert_intent_order_before(self._layout, "comparison", "ranking")

    def test_detail_last(self) -> None:
        _assert_detail_last(self._layout)


# ===========================================================================
# Scenario C — Cohort Recovery Dashboard (6 panels)
# ===========================================================================

_COHORT_PANELS: list[_PanelDef] = [
    ("kpi_r30", "SELECT AVG(recuperacion_30d) AS r30 FROM kpis_cobranza",
     [{"r30": 0.72}], [("r30", "DOUBLE")]),
    ("kpi_r60", "SELECT AVG(recuperacion_60d) AS r60 FROM kpis_cobranza",
     [{"r60": 0.81}], [("r60", "DOUBLE")]),
    ("kpi_r90", "SELECT AVG(recuperacion_90d) AS r90 FROM kpis_cobranza",
     [{"r90": 0.87}], [("r90", "DOUBLE")]),
    # Cohort heatmap: 2 GROUP BY (DATE + INTEGER) → cohort/line, col_span=12
    ("cohort_heatmap",
     "SELECT mes, bucket_dias, AVG(tasa_recuperacion) AS tasa "
     "FROM recuperacion_detail GROUP BY mes, bucket_dias ORDER BY mes",
     [{"mes": f"2024-{m:02d}-01", "bucket_dias": b, "tasa": 0.3 + m * 0.05}
      for m in range(1, 7) for b in [30, 60, 90]],
     [("mes", "DATE"), ("bucket_dias", "INTEGER"), ("tasa", "DOUBLE")]),
    # Cohort recovery curve: 2 GROUP BY (DATE + VARCHAR) → cohort/line, col_span=12
    ("cohort_curva",
     "SELECT mes, segmento, SUM(recuperacion) AS total "
     "FROM recuperacion_cohortes GROUP BY mes, segmento ORDER BY mes",
     [{"mes": f"2024-{m:02d}-01", "segmento": s, "total": 0.4 + m * 0.04}
      for m in range(1, 7) for s in ["Premium", "Free"]],
     [("mes", "DATE"), ("segmento", "VARCHAR"), ("total", "DOUBLE")]),
    # Cohort summary table
    ("detail_cohortes",
     "SELECT cohorte, bucket, monto_facturado, monto_cobrado, tasa FROM resumen_cohortes",
     None,
     [("cohorte", "DATE"), ("bucket", "VARCHAR"), ("monto_facturado", "DOUBLE"),
      ("monto_cobrado", "DOUBLE"), ("tasa", "DOUBLE")]),
]


class TestDashboardCohortRecovery:
    """Scenario C: 6-panel cohort recovery dashboard."""

    _results: ClassVar[list[tuple[str, InferenceResult]]]
    _layout: ClassVar[DashboardLayout]

    @classmethod
    def setup_class(cls) -> None:
        cls._results, cls._layout = _compose(_COHORT_PANELS)

    def test_all_panels_inferred(self) -> None:
        assert len(self._results) == 6

    def test_kpis_are_kpi(self) -> None:
        for pid, r in self._results:
            if pid.startswith("kpi_"):
                assert r.chart_winner == "kpi", f"{pid}: expected kpi, got {r.chart_winner}"

    def test_cohort_panels_are_line(self) -> None:
        for pid, r in self._results:
            if pid.startswith("cohort_"):
                assert r.intent_winner == "cohort", f"{pid}: expected cohort, got {r.intent_winner}"
                assert r.chart_winner == "line", f"{pid}: expected line, got {r.chart_winner}"

    def test_no_row_overflow(self) -> None:
        _assert_no_row_overflow(self._layout)

    def test_full_width_panels_alone(self) -> None:
        _assert_full_width_alone(self._layout)

    def test_kpis_lead(self) -> None:
        _assert_kpis_lead(self._layout)

    def test_kpi_row_has_three_kpis(self) -> None:
        """3 KPIs → 1 row, each col_span=4, total=12."""
        kpi_rows = [
            row for row in self._layout.rows
            if all(p.inference_result.chart_winner == "kpi" for p in row.panels)
        ]
        assert len(kpi_rows) == 1
        kpi_row = kpi_rows[0]
        assert len(kpi_row.panels) == 3
        assert kpi_row.total_span == 12
        assert all(p.final_col_span == 4 for p in kpi_row.panels)

    def test_cohort_wider_than_kpi(self) -> None:
        """Heatmap and curve panels must occupy more columns than each KPI panel."""
        kpi_span = next(
            p.final_col_span
            for row in self._layout.rows
            for p in row.panels
            if p.inference_result.chart_winner == "kpi"
        )
        for pid, r in self._results:
            if pid.startswith("cohort_"):
                panel = next(
                    p for row in self._layout.rows
                    for p in row.panels if p.panel_id == pid
                )
                assert panel.final_col_span > kpi_span, (
                    f"{pid} col_span={panel.final_col_span} is not wider than "
                    f"KPI col_span={kpi_span}"
                )

    def test_detail_last(self) -> None:
        _assert_detail_last(self._layout)

    def test_layout_has_4_rows(self) -> None:
        """3 KPIs (row 0) + 2 cohort lines (rows 1-2) + 1 detail (row 3) = 4 rows."""
        assert len(self._layout.rows) == 4


# ===========================================================================
# Scenario D — Many small KPIs (12 panels)
# ===========================================================================

_KPI12_PANELS: list[_PanelDef] = [
    (f"kpi_{i:02d}",
     f"SELECT SUM(metric_{i}) AS v FROM metrics",
     [{"v": float(i * 1000)}],
     [("v", "DOUBLE")])
    for i in range(1, 13)
]


class TestDashboard12KPIs:
    """Scenario D: 12 KPI-only dashboard — must group into 3 compact rows, not 12 single rows."""

    _results: ClassVar[list[tuple[str, InferenceResult]]]
    _layout: ClassVar[DashboardLayout]

    @classmethod
    def setup_class(cls) -> None:
        cls._results, cls._layout = _compose(_KPI12_PANELS)

    def test_all_12_panels_inferred(self) -> None:
        assert len(self._results) == 12

    def test_all_are_kpi(self) -> None:
        for pid, r in self._results:
            assert r.chart_winner == "kpi", f"{pid}: expected kpi, got {r.chart_winner}"

    def test_groups_into_3_rows(self) -> None:
        """12 KPIs in groups of 4 → exactly 3 rows (not 12 individual rows)."""
        assert len(self._layout.rows) == 3

    def test_each_row_has_4_kpis(self) -> None:
        for i, row in enumerate(self._layout.rows):
            assert len(row.panels) == 4, f"Row {i} has {len(row.panels)} panels, expected 4"

    def test_each_row_is_full_width(self) -> None:
        """4 × col_span=3 = 12 per row."""
        for i, row in enumerate(self._layout.rows):
            assert row.total_span == 12, f"Row {i} total_span={row.total_span}, expected 12"

    def test_all_kpi_col_spans_are_3(self) -> None:
        for row in self._layout.rows:
            for panel in row.panels:
                assert panel.final_col_span == 3, (
                    f"Panel '{panel.panel_id}' has col_span={panel.final_col_span}, expected 3"
                )

    def test_no_row_overflow(self) -> None:
        _assert_no_row_overflow(self._layout)


# ===========================================================================
# Scenario E — Mixed 100-panel stress test
# ===========================================================================

_KPI_NAMES = [
    "revenue", "orders", "customers", "nps", "mrr",
    "arr", "churn", "cac", "ltv", "conversion",
    "retention", "nrr", "gmv", "arpu", "dau",
]

_TREND_TARGETS = [
    "revenue", "orders", "sessions", "conversions", "signups",
    "cancellations", "tickets", "mrr", "arr", "nps",
    "dau", "mau", "arpu", "churn", "ltv",
    "cac", "gmv", "shipments", "returns", "refunds",
]

_COMP_CATEGORIES: list[list[str]] = [
    ["Norte", "Sur", "Este", "Oeste", "Centro"],
    ["Online", "Tienda", "Tel", "Partner", "Otro"],
    ["Premium", "Standard", "Basic", "Free", "Trial"],
    ["ProdA", "ProdB", "ProdC", "ProdD", "ProdE"],
    ["Cat1", "Cat2", "Cat3", "Cat4", "Cat5"],
    ["Zona1", "Zona2", "Zona3", "Zona4", "Zona5"],
    ["ES", "MX", "CO", "AR", "PE"],
    ["TipoA", "TipoB", "TipoC", "TipoD", "TipoE"],
    ["MarcaX", "MarcaY", "MarcaZ", "MarcaW", "MarcaV"],
    ["iOS", "Android", "Web", "API", "SDK"],
    ["L1", "L2", "L3", "L4", "L5"],
    ["Retail", "BFSI", "Health", "Tech", "Gov"],
    ["Activo", "Inactivo", "Pendiente", "Cancelado", "Trial"],
    ["C1", "C2", "C3", "C4", "C5"],
    ["D1", "D2", "D3", "D4", "D5"],
]

_COMPOSITION_CATS: list[list[str]] = [
    ["Premium", "Standard", "Basic"],
    ["Efectivo", "Tarjeta", "Transferencia"],
    ["Activo", "Inactivo", "Suspendido"],
    ["Anual", "Mensual", "Diario"],
    ["Femenino", "Masculino", "Otro"],
    ["Organico", "Pago", "Referido"],
    ["Nuevo", "Recurrente", "Reactivado"],
    ["Completado", "Pendiente", "Rechazado"],
]

_FUNNEL_STAGES: list[list[str]] = [
    ["Visita", "Lead", "Prueba", "Compra"],
    ["Registro", "Perfil", "Primer_uso", "Activo"],
    ["Inscripcion", "Configuracion", "Primera_accion", "Convertido"],
]

_DETAIL_TABLES = [
    "transacciones", "clientes", "pedidos", "productos",
    "facturas", "contratos", "tickets", "incidencias",
]


def _build_mixed_100_panels() -> list[_PanelDef]:
    """
    Build exactly 100 synthetic panels.
    Mix: 15 KPI + 20 trend + 15 comparison + 8 composition + 8 distribution
         + 10 ranking + 8 cohort + 5 anomaly + 3 funnel + 8 detail = 100.
    """
    panels: list[_PanelDef] = []

    # 15 KPIs — single aggregate, 1-row result → kpi/kpi
    for i, name in enumerate(_KPI_NAMES):
        kpi_data: list[dict[str, object]] = [{"v": float((i + 1) * 10000)}]
        panels.append((
            f"kpi_{i:02d}_{name}",
            f"SELECT SUM({name}) AS v FROM metrics",
            kpi_data,
            [("v", "DOUBLE")],
        ))

    # 20 Trends — monthly GROUP BY + SUM, 12 rows → trend/line
    for i, target in enumerate(_TREND_TARGETS):
        trend_data: list[dict[str, object]] = [
            {"mes": f"2024-{m:02d}-01", "total": float((i + 1) * 500 + m * 100)}
            for m in range(1, 13)
        ]
        panels.append((
            f"trend_{i:02d}_{target}",
            (
                f"SELECT mes, SUM({target}) AS total "
                f"FROM {target}_data GROUP BY mes ORDER BY mes"
            ),
            trend_data,
            [("mes", "DATE"), ("total", "DOUBLE")],
        ))

    # 15 Comparisons — 5 categories → comparison/bar (col_span=12)
    for i, cats in enumerate(_COMP_CATEGORIES):
        comp_data: list[dict[str, object]] = [
            {"category": c, "total": float((i + 1) * 8000 + j * 1500)}
            for j, c in enumerate(cats)
        ]
        panels.append((
            f"comp_{i:02d}",
            f"SELECT category, SUM(revenue) AS total FROM sales_{i} GROUP BY category",
            comp_data,
            [("category", "VARCHAR"), ("total", "DOUBLE")],
        ))

    # 8 Compositions — 3 categories (low_cardinality=1) → composition/pie (col_span=4)
    for i, cats3 in enumerate(_COMPOSITION_CATS):
        pie_data: list[dict[str, object]] = [
            {"cat": c, "n": float((i + 1) * 100 + j * 50)}
            for j, c in enumerate(cats3)
        ]
        panels.append((
            f"composition_{i:02d}",
            f"SELECT cat, COUNT(*) AS n FROM group_{i} GROUP BY cat",
            pie_data,
            [("cat", "VARCHAR"), ("n", "BIGINT")],
        ))

    # 8 Distributions — single numeric column, 20 rows → distribution/histogram (col_span=6)
    for i in range(8):
        dist_data: list[dict[str, object]] = [
            {"val": float(10 + j * 5 + i * 0.5)} for j in range(20)
        ]
        panels.append((
            f"dist_{i:02d}",
            f"SELECT val FROM measurements_{i}",
            dist_data,
            [("val", "DOUBLE")],
        ))

    # 10 Rankings — ORDER BY DESC LIMIT 10, high cardinality → col_span=12
    for i in range(10):
        rank_data: list[dict[str, object]] = [
            {"category": f"Item{j:02d}", "total": float((10 - j) * (i + 1) * 5000)}
            for j in range(10)
        ]
        panels.append((
            f"ranking_{i:02d}",
            (
                f"SELECT category, SUM(revenue) AS total FROM rank_data_{i} "
                f"GROUP BY category ORDER BY total DESC LIMIT 10"
            ),
            rank_data,
            [("category", "VARCHAR"), ("total", "DOUBLE")],
        ))

    # 8 Cohorts — 2 GROUP BY (DATE + VARCHAR) → cohort/line (col_span=12)
    for i in range(8):
        cohort_data: list[dict[str, object]] = [
            {"mes": f"2024-{m:02d}-01", "dim": seg, "valor": float((i + 1) * 50 + m * 10)}
            for m in range(1, 7)
            for seg in ["A", "B", "C"]
        ]
        panels.append((
            f"cohort_{i:02d}",
            (
                f"SELECT mes, dim, SUM(valor) AS valor FROM cohort_src_{i} "
                f"GROUP BY mes, dim ORDER BY mes"
            ),
            cohort_data,
            [("mes", "DATE"), ("dim", "VARCHAR"), ("valor", "DOUBLE")],
        ))

    # 5 Anomalies — 12 months with spike (Z > 3) → anomaly/line (col_span=12)
    for i in range(5):
        base = float((i + 1) * 1000)
        anom_data: list[dict[str, object]] = [
            {"mes": f"2024-{m:02d}-01", "total": base + m * 10.0}
            for m in range(1, 12)
        ] + [{"mes": "2024-12-01", "total": base * 8.0}]
        panels.append((
            f"anomaly_{i:02d}",
            (
                f"SELECT mes, SUM(metric_{i}) AS total "
                f"FROM anomaly_src_{i} GROUP BY mes ORDER BY mes"
            ),
            anom_data,
            [("mes", "DATE"), ("total", "DOUBLE")],
        ))

    # 3 Funnels — CASE WHEN 4 stages → funnel/bar (col_span=12)
    for i, stages in enumerate(_FUNNEL_STAGES):
        funnel_data: list[dict[str, object]] = [
            {"fase": s, "usuarios": float((4 - j) * (i + 1) * 2000)}
            for j, s in enumerate(stages)
        ]
        panels.append((
            f"funnel_{i:02d}",
            (
                f"SELECT CASE WHEN paso=1 THEN '{stages[0]}'"
                f" WHEN paso=2 THEN '{stages[1]}'"
                f" WHEN paso=3 THEN '{stages[2]}'"
                f" ELSE '{stages[3]}' END AS fase,"
                f" COUNT(*) AS usuarios FROM funnel_src_{i} GROUP BY 1"
            ),
            funnel_data,
            [("fase", "VARCHAR"), ("usuarios", "BIGINT")],
        ))

    # 8 Details — wide SELECT, no aggregation → detail/table (col_span=12)
    for i, table in enumerate(_DETAIL_TABLES):
        panels.append((
            f"detail_{i:02d}_{table}",
            f"SELECT id, fecha, nombre, monto, estado, categoria FROM {table}",
            None,
            [
                ("id", "BIGINT"), ("fecha", "DATE"), ("nombre", "VARCHAR"),
                ("monto", "DOUBLE"), ("estado", "VARCHAR"), ("categoria", "VARCHAR"),
            ],
        ))

    # 15+20+15+8+8+10+8+5+3+8 = 100
    return panels


_MIXED_100_PANELS: list[_PanelDef] = _build_mixed_100_panels()


class TestMixed100Panels:
    """
    Scenario E — 100-panel mixed stress test.

    Panel mix: 15 KPI + 20 trend + 15 comparison + 8 composition + 8 distribution
               + 10 ranking + 8 cohort + 5 anomaly + 3 funnel + 8 detail = 100.

    Layout quality criterion: packing occurred when len(layout.rows) < panel_count.
    Composition panels (col_span=4) pack 3/row; distribution panels (col_span=6)
    pack 2/row. Together these 16 panels save at least 10 rows, guaranteeing that
    row count < panel count. Expected: ~80 rows for 100 panels.
    """

    _results: ClassVar[list[tuple[str, InferenceResult]]]
    _layout: ClassVar[DashboardLayout]

    @classmethod
    def setup_class(cls) -> None:
        cls._results, cls._layout = _compose(_MIXED_100_PANELS)

    # --- Invariant 1: no exception ----------------------------------------

    def test_no_exception(self) -> None:
        """setup_class completes without raising — layout object exists."""
        assert self._layout is not None

    # --- Invariant 2: each panel exactly once ----------------------------

    def test_each_panel_exactly_once(self) -> None:
        panel_ids = [p.panel_id for row in self._layout.rows for p in row.panels]
        assert len(panel_ids) == 100, f"Expected 100 panels, got {len(panel_ids)}"
        assert len(set(panel_ids)) == 100, "Duplicate panel_ids in layout"

    # --- Invariant 3: no row exceeds 12 columns --------------------------

    def test_no_row_overflow(self) -> None:
        _assert_no_row_overflow(self._layout)

    # --- Invariant 4: full-width panels alone in row ----------------------

    def test_full_width_panels_alone(self) -> None:
        _assert_full_width_alone(self._layout)

    # --- Invariant 5: KPI panels lead ------------------------------------

    def test_kpis_lead(self) -> None:
        _assert_kpis_lead(self._layout)

    # --- Invariant 6: detail panels last ---------------------------------

    def test_detail_last(self) -> None:
        _assert_detail_last(self._layout)

    # --- Invariant 7: layout quality — packing occurred ------------------

    def test_layout_quality_packing_occurred(self) -> None:
        """
        Packing criterion: composition (col_span=4) packs 3/row and distribution
        (col_span=6) packs 2/row. With 8+8=16 such panels the layout must have
        fewer rows than panels.
        """
        assert self._layout.panel_count == 100
        assert len(self._layout.rows) < self._layout.panel_count, (
            f"No packing: {len(self._layout.rows)} rows for "
            f"{self._layout.panel_count} panels"
        )

    # --- Property 1: shuffle preserves structural invariants -------------

    def test_shuffle_preserves_invariants(self) -> None:
        """Shuffling input panels (seed=42) must not break structural invariants."""
        shuffled = list(_MIXED_100_PANELS)
        random.Random(42).shuffle(shuffled)
        _, layout = _compose(shuffled)
        _assert_no_row_overflow(layout)
        _assert_full_width_alone(layout)
        _assert_kpis_lead(layout)
        _assert_detail_last(layout)
        ids = [p.panel_id for row in layout.rows for p in row.panels]
        assert len(ids) == 100 and len(set(ids)) == 100

    # --- Property 2: determinism -----------------------------------------

    def test_determinism(self) -> None:
        """Composing the same results list twice yields identical layouts."""
        layout_a = _engine.compose(self._results)
        layout_b = _engine.compose(self._results)
        assert len(layout_a.rows) == len(layout_b.rows)
        for row_a, row_b in zip(layout_a.rows, layout_b.rows):
            assert len(row_a.panels) == len(row_b.panels)
            for pa, pb in zip(row_a.panels, row_b.panels):
                assert pa.panel_id == pb.panel_id
                assert pa.final_col_span == pb.final_col_span
                assert pa.row_index == pb.row_index

    # --- Property 3: adding detail must not move KPIs --------------------

    def test_add_detail_does_not_move_kpis(self) -> None:
        """KPI row indices are unchanged when a new detail panel is appended."""
        base: list[_PanelDef] = list(_MIXED_100_PANELS[:20])  # 15 KPIs + 5 trends
        _, layout_base = _compose(base)
        kpi_rows_before = {
            p.row_index
            for row in layout_base.rows
            for p in row.panels
            if p.inference_result.chart_winner == "kpi"
        }
        extra: _PanelDef = (
            "detail_extra",
            "SELECT id, fecha, nombre, monto, estado, origen FROM extra",
            None,
            [
                ("id", "BIGINT"), ("fecha", "DATE"), ("nombre", "VARCHAR"),
                ("monto", "DOUBLE"), ("estado", "VARCHAR"), ("origen", "VARCHAR"),
            ],
        )
        _, layout_after = _compose(base + [extra])
        kpi_rows_after = {
            p.row_index
            for row in layout_after.rows
            for p in row.panels
            if p.inference_result.chart_winner == "kpi"
        }
        assert kpi_rows_before == kpi_rows_after, (
            f"KPI rows changed: {sorted(kpi_rows_before)} → {sorted(kpi_rows_after)}"
        )

    # --- Property 4: adding KPI inserts in KPI zone ----------------------

    def test_add_kpi_inserts_in_kpi_zone(self) -> None:
        """Adding one KPI to a KPI-free dashboard places it before all non-KPI rows."""
        non_kpi: list[_PanelDef] = list(_MIXED_100_PANELS[15:20])  # 5 trend panels
        _, layout_no_kpi = _compose(non_kpi)
        assert not any(
            p.inference_result.chart_winner == "kpi"
            for row in layout_no_kpi.rows
            for p in row.panels
        ), "Baseline must have no KPI panels"
        kpi_val: list[dict[str, object]] = [{"v": 999999.0}]
        new_kpi: _PanelDef = (
            "kpi_extra",
            "SELECT SUM(extra_revenue) AS v FROM extra_sales",
            kpi_val,
            [("v", "DOUBLE")],
        )
        _, layout_with_kpi = _compose(non_kpi + [new_kpi])
        kpi_rows = {
            p.row_index
            for row in layout_with_kpi.rows
            for p in row.panels
            if p.inference_result.chart_winner == "kpi"
        }
        other_rows = {
            p.row_index
            for row in layout_with_kpi.rows
            for p in row.panels
            if p.inference_result.chart_winner != "kpi"
        }
        assert kpi_rows, "KPI must appear after being added"
        assert max(kpi_rows) < min(other_rows), (
            f"KPI rows {sorted(kpi_rows)} must lead non-KPI rows {sorted(other_rows)}"
        )
