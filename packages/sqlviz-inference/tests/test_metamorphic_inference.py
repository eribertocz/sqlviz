"""Metamorphic inference tests — Entrega 3.B.

Each group defines a canonical SQL query and several semantically
equivalent variants.  The invariant: all variants in a group must
produce the same intent_winner and chart_winner as the base case.

Any variant that breaks stability without a conceptual reason is
documented as a new §16.x bug in DOC5.
"""

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.chart.chart_engine import ChartEngine
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.features.feature_engine import FeatureEngine
from sqlviz_inference.intent.intent_engine import IntentEngine
from sqlviz_inference.parser.sql_parser import SQLParser
from sqlviz_inference.semantic.semantic_engine import SemanticEngine

# ---------------------------------------------------------------------------
# Shared pipeline
# ---------------------------------------------------------------------------

_parser = SQLParser()
_features = FeatureEngine()
_semantic = SemanticEngine()
_intent = IntentEngine()
_chart = ChartEngine()


def _infer(
    sql: str,
    data: list[dict[str, object]] | None = None,
    schema_defs: list[tuple[str, str]] | None = None,
) -> RuntimeContext:
    schema = [ColumnSchema(name=n, type=t) for n, t in (schema_defs or [])]
    ctx = RuntimeContext(sql=sql, data=data or [], schema=schema)
    ctx = _parser.run(ctx)
    ctx = _features.run(ctx)
    ctx = _semantic.run(ctx)
    ctx = _intent.run(ctx)
    ctx = _chart.run(ctx)
    return ctx


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

# Trend: 12 monthly rows, no outlier
_TREND_DATA: list[dict[str, object]] = [
    {"mes": f"2024-{i:02d}-01", "monto": i * 1000} for i in range(1, 13)
]
_TREND_SCHEMA = [("mes", "DATE"), ("monto", "DOUBLE")]

# Comparison: 5 categories (> 3 → low_cardinality does not fire → comparison)
_COMP_DATA: list[dict[str, object]] = [
    {"categoria": "A", "monto": 45000},
    {"categoria": "B", "monto": 32000},
    {"categoria": "C", "monto": 28000},
    {"categoria": "D", "monto": 19000},
    {"categoria": "E", "monto": 12000},
]
_COMP_SCHEMA = [("categoria", "VARCHAR"), ("monto", "DOUBLE")]

# Ranking: 10 clients, descending debt
_RANK_DATA: list[dict[str, object]] = [
    {"cliente": f"C{i}", "deuda": (10 - i) * 10000.0} for i in range(10)
]
_RANK_SCHEMA = [("cliente", "VARCHAR"), ("deuda", "DOUBLE")]

# Distribution: 20 single-metric rows
_DIST_DATA: list[dict[str, object]] = [
    {"consumo_kwh": float(v)}
    for v in [120, 95, 200, 310, 88, 145, 178, 92, 267, 156,
              203, 134, 99, 185, 222, 108, 165, 290, 143, 117]
]
_DIST_SCHEMA = [("consumo_kwh", "DOUBLE")]

# KPI: single-row result — engine sees result_row_count_is_1=1
_KPI_DATA: list[dict[str, object]] = [{"recuperacion": 0.87}]
_KPI_SCHEMA = [("recuperacion", "DOUBLE")]

# Composition (structural share formula): 3 categories
_POW_DATA: list[dict[str, object]] = [
    {"categoria": "A", "monto": 45000.0},
    {"categoria": "B", "monto": 35000.0},
    {"categoria": "C", "monto": 20000.0},
]
_POW_SCHEMA = [("categoria", "VARCHAR"), ("monto", "DOUBLE")]

# Detail: 6 columns, raw rows
_DETAIL_SCHEMA = [
    ("consumidor", "VARCHAR"),
    ("medidor", "VARCHAR"),
    ("categoria", "VARCHAR"),
    ("area", "VARCHAR"),
    ("fecha_emision", "DATE"),
    ("monto", "DOUBLE"),
]

# Cohort: 2 GROUP BY dimensions (DATE + VARCHAR) — triggers group_by_count_gte_2
_COHORT_DATA: list[dict[str, object]] = [
    {"mes": "2024-01-01", "segmento": "Premium", "usuarios": 450},
    {"mes": "2024-01-01", "segmento": "Free", "usuarios": 1200},
    {"mes": "2024-02-01", "segmento": "Premium", "usuarios": 480},
    {"mes": "2024-02-01", "segmento": "Free", "usuarios": 1350},
    {"mes": "2024-03-01", "segmento": "Premium", "usuarios": 510},
    {"mes": "2024-03-01", "segmento": "Free", "usuarios": 1420},
]
_COHORT_SCHEMA = [("mes", "DATE"), ("segmento", "VARCHAR"), ("usuarios", "BIGINT")]

# Anomaly: 12 monthly rows with December spike (Z≈3.17 > 3.0).
# Schema uses result column names (mes + total) to align with data keys.
_ANOMALY_DATA: list[dict[str, object]] = [
    {"mes": "2024-01-01", "total": 98000.0},
    {"mes": "2024-02-01", "total": 102000.0},
    {"mes": "2024-03-01", "total": 99500.0},
    {"mes": "2024-04-01", "total": 103000.0},
    {"mes": "2024-05-01", "total": 101000.0},
    {"mes": "2024-06-01", "total": 97000.0},
    {"mes": "2024-07-01", "total": 100000.0},
    {"mes": "2024-08-01", "total": 104000.0},
    {"mes": "2024-09-01", "total": 99000.0},
    {"mes": "2024-10-01", "total": 102000.0},
    {"mes": "2024-11-01", "total": 100000.0},
    {"mes": "2024-12-01", "total": 485000.0},   # spike
]
_ANOMALY_SCHEMA = [("mes", "DATE"), ("total", "DOUBLE")]

# Funnel: CASE WHEN expression is the funnel signal (§ intent_rules)
_FUNNEL_DATA: list[dict[str, object]] = [
    {"etapa": "Visitante", "usuarios": 10000},
    {"etapa": "Registro", "usuarios": 4200},
    {"etapa": "Compra", "usuarios": 1800},
    {"etapa": "Abandono", "usuarios": 4000},
]
_FUNNEL_SCHEMA = [("etapa", "VARCHAR"), ("usuarios", "BIGINT")]

_FUNNEL_CASE = (
    "CASE WHEN etapa = 1 THEN 'Visitante' "
    "WHEN etapa = 2 THEN 'Registro' "
    "WHEN etapa = 3 THEN 'Compra' "
    "ELSE 'Abandono' END"
)


# ===========================================================================
# Group 1 — Trend mensual
# ===========================================================================


class TestMetamorphicTrend:
    """SELECT mes, SUM(monto) … GROUP BY mes ORDER BY mes → trend / line."""

    _EXPECTED_INTENT = "trend"
    _EXPECTED_CHART = "line"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT mes, SUM(monto) AS total FROM ventas GROUP BY mes ORDER BY mes",
            _TREND_DATA, _TREND_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_group_by_positional(self) -> None:
        """GROUP BY 1 is positionally equivalent to GROUP BY mes."""
        ctx = _infer(
            "SELECT mes, SUM(monto) AS total FROM ventas GROUP BY 1 ORDER BY 1",
            _TREND_DATA, _TREND_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_differs(self) -> None:
        """Renaming the aggregate alias does not change intent."""
        ctx = _infer(
            "SELECT mes, SUM(monto) AS ingresos_totales FROM ventas GROUP BY mes ORDER BY mes",
            _TREND_DATA, _TREND_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_where_filter(self) -> None:
        """Adding WHERE monto > 0 does not change intent (same SQL shape)."""
        ctx = _infer(
            "SELECT mes, SUM(monto) AS total FROM ventas WHERE monto > 0 GROUP BY mes ORDER BY mes",
            _TREND_DATA, _TREND_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_cte(self) -> None:
        """Lifting source to a CTE preserves structural features."""
        ctx = _infer(
            "WITH datos AS (SELECT mes, monto FROM ventas) "
            "SELECT mes, SUM(monto) AS total FROM datos GROUP BY mes ORDER BY mes",
            _TREND_DATA, _TREND_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_date_trunc(self) -> None:
        """DATE_TRUNC expression on the time column keeps temporal dimension."""
        ctx = _infer(
            "SELECT DATE_TRUNC('month', mes) AS mes, SUM(monto) AS total "
            "FROM ventas GROUP BY 1 ORDER BY 1",
            _TREND_DATA, _TREND_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 2 — Comparison por categoría
# ===========================================================================


class TestMetamorphicComparison:
    """SELECT categoria, SUM(monto) … GROUP BY categoria → comparison / bar."""

    _EXPECTED_INTENT = "comparison"
    _EXPECTED_CHART = "bar"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT categoria, SUM(monto) AS total FROM ventas GROUP BY categoria",
            _COMP_DATA, _COMP_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_total_ventas(self) -> None:
        ctx = _infer(
            "SELECT categoria, SUM(monto) AS total_ventas FROM ventas GROUP BY categoria",
            _COMP_DATA, _COMP_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_order_by_desc(self) -> None:
        """ORDER BY total DESC on a comparison query keeps it comparison, not ranking
        (no LIMIT → ranking boost fails)."""
        ctx = _infer(
            "SELECT categoria, SUM(monto) AS total FROM ventas "
            "GROUP BY categoria ORDER BY total DESC",
            _COMP_DATA, _COMP_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_having(self) -> None:
        """HAVING SUM(monto) > 0 is a structural no-op for non-empty data."""
        ctx = _infer(
            "SELECT categoria, SUM(monto) AS total FROM ventas "
            "GROUP BY categoria HAVING SUM(monto) > 0",
            _COMP_DATA, _COMP_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_subquery(self) -> None:
        """Wrapping in a subquery does not change the effective query shape."""
        ctx = _infer(
            "SELECT * FROM ("
            "SELECT categoria, SUM(monto) AS total FROM ventas GROUP BY categoria"
            ") AS sub",
            _COMP_DATA, _COMP_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 3 — Ranking top N
# ===========================================================================


class TestMetamorphicRanking:
    """SELECT cliente, SUM(deuda) … ORDER BY deuda DESC LIMIT 10 → ranking / bar_horizontal."""

    _EXPECTED_INTENT = "ranking"
    _EXPECTED_CHART = "bar_horizontal"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT cliente, SUM(deuda) AS deuda FROM cartera "
            "GROUP BY cliente ORDER BY deuda DESC LIMIT 10",
            _RANK_DATA, _RANK_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_positional_order_by(self) -> None:
        """ORDER BY 2 DESC is positionally equivalent to ORDER BY deuda DESC."""
        ctx = _infer(
            "SELECT cliente, SUM(deuda) AS deuda FROM cartera "
            "GROUP BY cliente ORDER BY 2 DESC LIMIT 10",
            _RANK_DATA, _RANK_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_sum_expr_in_order_by(self) -> None:
        """ORDER BY SUM(deuda) DESC is semantically the same as ORDER BY alias."""
        ctx = _infer(
            "SELECT cliente, SUM(deuda) AS deuda FROM cartera "
            "GROUP BY cliente ORDER BY SUM(deuda) DESC LIMIT 10",
            _RANK_DATA, _RANK_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_renamed(self) -> None:
        """Renaming the metric alias does not affect the ranking pattern."""
        ctx = _infer(
            "SELECT cliente, SUM(deuda) AS total_deuda FROM cartera "
            "GROUP BY cliente ORDER BY total_deuda DESC LIMIT 10",
            _RANK_DATA, _RANK_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 4 — Distribution (histograma)
# ===========================================================================


class TestMetamorphicDistribution:
    """SELECT consumo_kwh FROM facturacion → distribution / histogram."""

    _EXPECTED_INTENT = "distribution"
    _EXPECTED_CHART = "histogram"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT consumo_kwh FROM facturacion",
            _DIST_DATA, _DIST_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_cast_double(self) -> None:
        """CAST to DOUBLE is a no-op for a column already typed DOUBLE."""
        ctx = _infer(
            "SELECT CAST(consumo_kwh AS DOUBLE) AS consumo_kwh FROM facturacion",
            _DIST_DATA, _DIST_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_where_positive(self) -> None:
        """Filtering out zeros does not change the single-numeric distribution shape."""
        ctx = _infer(
            "SELECT consumo_kwh FROM facturacion WHERE consumo_kwh > 0",
            _DIST_DATA, _DIST_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_consumo(self) -> None:
        """Renaming the column alias keeps the distribution signal intact."""
        ctx = _infer(
            "SELECT consumo_kwh AS consumo FROM facturacion",
            [{"consumo": d["consumo_kwh"]} for d in _DIST_DATA],
            [("consumo", "DOUBLE")],
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 5 — KPI (single scalar)
# ===========================================================================


class TestMetamorphicKPI:
    """SELECT SUM(cobrado)/SUM(facturado) AS recuperacion → kpi / kpi.

    Requires single-row result data so that result_row_count_is_1=1 fires.
    """

    _EXPECTED_INTENT = "kpi"
    _EXPECTED_CHART = "kpi"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT SUM(cobrado) / SUM(facturado) AS recuperacion FROM cobranza",
            _KPI_DATA, _KPI_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_pct(self) -> None:
        ctx = _infer(
            "SELECT SUM(cobrado) / SUM(facturado) AS pct_recuperacion FROM cobranza",
            [{"pct_recuperacion": 0.87}],
            [("pct_recuperacion", "DOUBLE")],
        )
        self._assert_stable(ctx)

    def test_variant_round(self) -> None:
        """ROUND wrapping does not change the single-aggregate KPI pattern."""
        ctx = _infer(
            "SELECT ROUND(SUM(cobrado) / SUM(facturado), 4) AS recuperacion FROM cobranza",
            _KPI_DATA, _KPI_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_cte(self) -> None:
        """CTE that resolves to a single scalar row still reads as KPI."""
        ctx = _infer(
            "WITH base AS (SELECT SUM(cobrado) AS c, SUM(facturado) AS f FROM cobranza) "
            "SELECT c / f AS recuperacion FROM base",
            _KPI_DATA, _KPI_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 6 — Composition fuerte (señal estructural §16.21)
# ===========================================================================


class TestMetamorphicComposition:
    """Share formula x/SUM(x) OVER() → composition / pie."""

    _EXPECTED_INTENT = "composition"
    _EXPECTED_CHART = "pie"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT categoria, SUM(monto) / SUM(SUM(monto)) OVER () AS participacion "
            "FROM ventas GROUP BY categoria",
            _POW_DATA, _POW_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_cuota(self) -> None:
        """Alias 'cuota' does not weaken the AST structural signal."""
        ctx = _infer(
            "SELECT categoria, SUM(monto) / SUM(SUM(monto)) OVER () AS cuota "
            "FROM ventas GROUP BY categoria",
            _POW_DATA, _POW_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_share(self) -> None:
        """Alias 'share' (positive name) also stays composition."""
        ctx = _infer(
            "SELECT categoria, SUM(monto) / SUM(SUM(monto)) OVER () AS share "
            "FROM ventas GROUP BY categoria",
            _POW_DATA, _POW_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 7 — Detail (raw rows)
# ===========================================================================


class TestMetamorphicDetail:
    """Wide SELECT without aggregation → detail / table."""

    _EXPECTED_INTENT = "detail"
    _EXPECTED_CHART = "table"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART
        assert ctx.intent_quality in ("medium", "high")

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT consumidor, medidor, categoria, area, fecha_emision, monto "
            "FROM facturacion",
            schema_defs=_DETAIL_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_where_filter(self) -> None:
        """Adding a WHERE clause does not change the raw-rows intent."""
        ctx = _infer(
            "SELECT consumidor, medidor, categoria, area, fecha_emision, monto "
            "FROM facturacion WHERE area = 'Norte'",
            schema_defs=_DETAIL_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_limit(self) -> None:
        """LIMIT without ORDER BY DESC + aggregation → not ranking → still detail."""
        ctx = _infer(
            "SELECT consumidor, medidor, categoria, area, fecha_emision, monto "
            "FROM facturacion LIMIT 100",
            schema_defs=_DETAIL_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 8 — Cohort (2 GROUP BY: DATE + VARCHAR)
# ===========================================================================


class TestMetamorphicCohort:
    """SELECT mes, segmento, COUNT(*) … GROUP BY mes, segmento → cohort / line.

    §16.27 BUG: GROUP BY 1, 2 (positional integers) makes count_group_by_columns
    return 0 because ast_helpers.count_group_by_columns counts exp.Column nodes only.
    Positional references are exp.Literal nodes → group_by_count_gte_2 does not fire
    → cohort drops below trend → intent flips to trend.
    Root cause: count_group_by_columns in ast_helpers.py:100 only calls
    group.find_all(exp.Column); it must also handle positional integer literals
    by resolving them to the referenced SELECT columns.
    """

    _EXPECTED_INTENT = "cohort"
    _EXPECTED_CHART = "line"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT mes, segmento, COUNT(*) AS usuarios FROM suscripciones "
            "GROUP BY mes, segmento ORDER BY mes",
            _COHORT_DATA, _COHORT_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_group_by_positional(self) -> None:
        """GROUP BY 1, 2 is equivalent to GROUP BY mes, segmento (§16.27 fix)."""
        ctx = _infer(
            "SELECT mes, segmento, COUNT(*) AS usuarios FROM suscripciones "
            "GROUP BY 1, 2 ORDER BY 1",
            _COHORT_DATA, _COHORT_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_total_usuarios(self) -> None:
        """Renaming COUNT alias does not affect the 2-GROUP-BY cohort signal."""
        ctx = _infer(
            "SELECT mes, segmento, COUNT(*) AS total_usuarios FROM suscripciones "
            "GROUP BY mes, segmento ORDER BY mes",
            [{"mes": d["mes"], "segmento": d["segmento"], "total_usuarios": d["usuarios"]}
             for d in _COHORT_DATA],
            [("mes", "DATE"), ("segmento", "VARCHAR"), ("total_usuarios", "BIGINT")],
        )
        self._assert_stable(ctx)

    def test_variant_sum_instead_of_count(self) -> None:
        """SUM instead of COUNT preserves the cohort structural pattern."""
        ctx = _infer(
            "SELECT mes, segmento, SUM(usuarios) AS usuarios FROM suscripciones "
            "GROUP BY mes, segmento ORDER BY mes",
            _COHORT_DATA, _COHORT_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 9 — Anomaly (outlier spike)
# ===========================================================================


class TestMetamorphicAnomaly:
    """Monthly series with December spike (Z≈3.17 > 3.0) → anomaly / line.

    NOTE: schema must use result column names (mes + total) matching data keys
    so the feature engine can read the numeric values for Z-score detection.
    """

    _EXPECTED_INTENT = "anomaly"
    _EXPECTED_CHART = "line"

    def _assert_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == self._EXPECTED_CHART

    def test_base(self) -> None:
        ctx = _infer(
            "SELECT mes, SUM(monto) AS total FROM ventas GROUP BY mes ORDER BY mes",
            _ANOMALY_DATA, _ANOMALY_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_alias_total_mensual(self) -> None:
        """Alias rename preserves outlier data values — anomaly detection is data-driven."""
        ctx = _infer(
            "SELECT mes, SUM(monto) AS total_mensual FROM ventas GROUP BY mes ORDER BY mes",
            [{**d, "total_mensual": d["total"]} for d in _ANOMALY_DATA],
            [("mes", "DATE"), ("total_mensual", "DOUBLE")],
        )
        self._assert_stable(ctx)

    def test_variant_where_filter(self) -> None:
        """WHERE filter with same spike data still triggers anomaly detection."""
        ctx = _infer(
            "SELECT mes, SUM(monto) AS total FROM ventas "
            "WHERE monto > 0 GROUP BY mes ORDER BY mes",
            _ANOMALY_DATA, _ANOMALY_SCHEMA,
        )
        self._assert_stable(ctx)

    def test_variant_cte(self) -> None:
        """CTE wrapper does not strip the outlier information from data."""
        ctx = _infer(
            "WITH datos AS (SELECT mes, monto FROM ventas) "
            "SELECT mes, SUM(monto) AS total FROM datos GROUP BY mes ORDER BY mes",
            _ANOMALY_DATA, _ANOMALY_SCHEMA,
        )
        self._assert_stable(ctx)


# ===========================================================================
# Group 10 — Funnel (CASE WHEN is the key signal)
# ===========================================================================


class TestMetamorphicFunnel:
    """CASE WHEN stage classification + COUNT(*) → funnel.

    Chart note: ORDER BY COUNT(*) DESC legitimately shifts chart from bar to
    bar_horizontal (ranking signal boosts bar_horizontal in chart engine).
    The INTENT invariant (funnel) holds for all variants; chart is allowed to
    be 'bar' or 'bar_horizontal' — both are semantically valid for funnels
    (see adv_fun_001 / adv_fun_004 in adversarial benchmark).
    """

    _EXPECTED_INTENT = "funnel"

    def _assert_intent_stable(self, ctx: RuntimeContext) -> None:
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner in ("bar", "bar_horizontal")

    def test_base(self) -> None:
        ctx = _infer(
            f"SELECT {_FUNNEL_CASE} AS etapa, COUNT(*) AS usuarios "
            "FROM funnel_cobranza GROUP BY 1",
            _FUNNEL_DATA, _FUNNEL_SCHEMA,
        )
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == "bar"

    def test_variant_alias_clientes(self) -> None:
        """Renaming COUNT alias does not remove the CASE WHEN funnel signal."""
        ctx = _infer(
            f"SELECT {_FUNNEL_CASE} AS etapa, COUNT(*) AS clientes "
            "FROM funnel_cobranza GROUP BY 1",
            [{"etapa": d["etapa"], "clientes": d["usuarios"]} for d in _FUNNEL_DATA],
            [("etapa", "VARCHAR"), ("clientes", "BIGINT")],
        )
        self._assert_intent_stable(ctx)

    def test_variant_order_by_desc_chart_shifts(self) -> None:
        """Adding ORDER BY COUNT(*) DESC keeps intent=funnel; chart shifts to
        bar_horizontal (ORDER BY DESC boosts bar_horizontal in chart engine —
        same behaviour as adv_fun_004). Intent stability is preserved."""
        ctx = _infer(
            f"SELECT {_FUNNEL_CASE} AS etapa, COUNT(*) AS usuarios "
            "FROM funnel_cobranza GROUP BY 1 ORDER BY COUNT(*) DESC",
            _FUNNEL_DATA, _FUNNEL_SCHEMA,
        )
        assert ctx.intent_winner == self._EXPECTED_INTENT
        assert ctx.chart_winner == "bar_horizontal"

    def test_variant_cte(self) -> None:
        """CTE wrapping preserves the CASE WHEN node in the AST."""
        ctx = _infer(
            f"WITH etapas AS (SELECT {_FUNNEL_CASE} AS etapa, "
            "COUNT(*) AS usuarios FROM funnel_cobranza GROUP BY 1) "
            "SELECT etapa, usuarios FROM etapas",
            _FUNNEL_DATA, _FUNNEL_SCHEMA,
        )
        self._assert_intent_stable(ctx)
