"""Intent Engine tests — DOC5 Section 7.4."""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.features.feature_engine import FeatureEngine
from sqlviz_inference.intent.intent_engine import IntentEngine
from sqlviz_inference.parser.sql_parser import SQLParser
from sqlviz_inference.semantic.semantic_engine import SemanticEngine

parser = SQLParser()
features = FeatureEngine()
semantic = SemanticEngine()
intent = IntentEngine()


def infer_intent(
    sql: str,
    data: list[dict[str, object]] | None = None,
    schema_defs: list[tuple[str, str]] | None = None,
) -> RuntimeContext:
    schema = (
        [ColumnSchema(name=n, type=t) for n, t in schema_defs]
        if schema_defs
        else []
    )
    ctx = RuntimeContext(sql=sql, data=data or [], schema=schema)
    ctx = parser.run(ctx)
    ctx = features.run(ctx)
    ctx = semantic.run(ctx)
    ctx = intent.run(ctx)
    return ctx


class TestTrendIntent:

    def test_monthly_revenue_is_trend(self) -> None:
        ctx = infer_intent(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month",
            data=[{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)],
            schema_defs=[("month", "DATE"), ("revenue", "DOUBLE")],
        )
        assert ctx.intent_winner == "trend"
        assert ctx.intent_raw_score > 0.70
        assert ctx.intent_quality == "high"

    def test_weekly_sales_is_trend(self) -> None:
        ctx = infer_intent(
            sql="SELECT week, SUM(ventas) FROM ventas GROUP BY week ORDER BY week",
            schema_defs=[("week", "DATE"), ("ventas", "DOUBLE")],
        )
        assert ctx.intent_winner == "trend"


class TestKPIIntent:

    def test_single_sum_is_kpi(self) -> None:
        ctx = infer_intent(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
            schema_defs=[("total", "DOUBLE")],
        )
        assert ctx.intent_winner == "kpi"
        assert ctx.intent_raw_score > 0.70

    def test_count_all_is_kpi(self) -> None:
        ctx = infer_intent(
            sql="SELECT COUNT(*) AS total_orders FROM orders",
            data=[{"total_orders": 4521}],
            schema_defs=[("total_orders", "BIGINT")],
        )
        assert ctx.intent_winner == "kpi"

    # ── D0 mode (sql-only, no schema, no data) ──────────────────────────────
    # §16.28: kpi must win from SQL structure alone (has_aggregation + no_group_by)
    # when no data is available. The removed multiple_rows penalty was firing on
    # every D0 query, making kpi unreachable in sql-only mode.

    def test_count_star_d0_is_kpi(self) -> None:
        """SELECT COUNT(*) FROM orders with no data → kpi (D0 mode)."""
        ctx = infer_intent(sql="SELECT COUNT(*) FROM orders")
        assert ctx.intent_winner == "kpi"
        assert ctx.intent_raw_score > 0.40

    def test_sum_d0_is_kpi(self) -> None:
        """SELECT SUM(revenue) FROM sales with no data → kpi (D0 mode)."""
        ctx = infer_intent(sql="SELECT SUM(revenue) FROM sales")
        assert ctx.intent_winner == "kpi"
        assert ctx.intent_raw_score > 0.40

    def test_avg_d0_is_kpi(self) -> None:
        """SELECT AVG(price) FROM products with no data → kpi (D0 mode)."""
        ctx = infer_intent(sql="SELECT AVG(price) FROM products")
        assert ctx.intent_winner == "kpi"
        assert ctx.intent_raw_score > 0.40


class TestRankingIntent:

    def test_top_products_is_ranking(self) -> None:
        ctx = infer_intent(
            sql="SELECT product, SUM(revenue) FROM sales "
                "GROUP BY product ORDER BY 2 DESC LIMIT 10",
            schema_defs=[("product", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        assert ctx.intent_winner == "ranking"
        assert ctx.intent_raw_score > 0.60

    def test_ranking_boost_applied(self) -> None:
        ctx = infer_intent(
            sql="SELECT cat, COUNT(*) FROM t GROUP BY cat ORDER BY 2 DESC LIMIT 5",
            schema_defs=[("cat", "VARCHAR"), ("count", "BIGINT")],
        )
        assert ctx.intent_winner == "ranking"


class TestComparisonIntent:

    def test_category_comparison(self) -> None:
        ctx = infer_intent(
            sql="SELECT region, SUM(revenue) FROM sales GROUP BY region",
            schema_defs=[("region", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        assert ctx.intent_winner in ("comparison", "composition")

    def test_no_temporal_favors_comparison(self) -> None:
        ctx = infer_intent(
            sql="SELECT category, COUNT(*) FROM products GROUP BY category",
            schema_defs=[("category", "VARCHAR"), ("count", "BIGINT")],
        )
        assert ctx.intent_winner in ("comparison", "ranking", "composition")


class TestDetailIntent:

    def test_select_star_is_detail(self) -> None:
        ctx = infer_intent(
            sql="SELECT id, name, email, phone, address FROM customers",
            schema_defs=[
                ("id", "INTEGER"),
                ("name", "VARCHAR"),
                ("email", "VARCHAR"),
                ("phone", "VARCHAR"),
                ("address", "VARCHAR"),
            ],
        )
        assert ctx.intent_winner == "detail"


class TestGroupByCountBoundary:
    """§16.22 — boundary tests for group_by_count_gte_2 (fixed from > to >=)."""

    def _gte2_value(self, ctx: RuntimeContext) -> float:
        signals: dict[str, object] = ctx.score_trace["intent"]["cohort"]["signals"]
        entry: dict[str, object] = signals.get("group_by_count_gte_2", {})  # type: ignore[assignment]
        return float(entry.get("value", 0.0))  # type: ignore[arg-type]

    def test_one_group_by_does_not_fire(self) -> None:
        ctx = infer_intent(
            sql="SELECT region, SUM(revenue) FROM sales GROUP BY region",
            schema_defs=[("region", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        assert self._gte2_value(ctx) == 0.0

    def test_two_group_by_fires(self) -> None:
        ctx = infer_intent(
            sql="SELECT mes, segmento, SUM(ingresos) FROM ventas GROUP BY mes, segmento",
            schema_defs=[("mes", "DATE"), ("segmento", "VARCHAR"), ("ingresos", "DOUBLE")],
        )
        assert self._gte2_value(ctx) == 1.0

    def test_three_group_by_fires(self) -> None:
        ctx = infer_intent(
            sql="SELECT mes, segmento, pais, SUM(v) FROM datos GROUP BY mes, segmento, pais",
            schema_defs=[
                ("mes", "DATE"), ("segmento", "VARCHAR"),
                ("pais", "VARCHAR"), ("v", "DOUBLE"),
            ],
        )
        assert self._gte2_value(ctx) == 1.0


class TestPartOfWholeScore:
    """§16.21 protective tests — composition/pie only wins with part-of-whole evidence."""

    def test_rate_column_recuperacion_pct_is_comparison(self) -> None:
        ctx = infer_intent(
            sql="SELECT area, AVG(recuperacion_pct) FROM cartera GROUP BY area",
            schema_defs=[("area", "VARCHAR"), ("recuperacion_pct", "DOUBLE")],
            data=[
                {"area": "Norte", "recuperacion_pct": 0.72},
                {"area": "Sur",   "recuperacion_pct": 0.68},
                {"area": "Este",  "recuperacion_pct": 0.81},
            ],
        )
        assert ctx.intent_winner == "comparison"

    def test_avg_metric_by_city_is_comparison_not_composition(self) -> None:
        ctx = infer_intent(
            sql="SELECT ciudad, AVG(salario) AS promedio FROM empleados GROUP BY ciudad",
            schema_defs=[("ciudad", "VARCHAR"), ("salario", "DOUBLE")],
            data=[
                {"ciudad": "Madrid",    "promedio": 45000},
                {"ciudad": "Barcelona", "promedio": 52000},
                {"ciudad": "Valencia",  "promedio": 38000},
            ],
        )
        assert ctx.intent_winner == "comparison"

    def test_participacion_column_name_is_composition(self) -> None:
        ctx = infer_intent(
            sql="SELECT categoria, COUNT(*) AS cantidad, participacion "
                "FROM ventas_resumen GROUP BY categoria",
            schema_defs=[
                ("categoria", "VARCHAR"),
                ("cantidad", "BIGINT"),
                ("participacion", "DOUBLE"),
            ],
            data=[
                {"categoria": "A", "cantidad": 450, "participacion": 0.45},
                {"categoria": "B", "cantidad": 350, "participacion": 0.35},
                {"categoria": "C", "cantidad": 200, "participacion": 0.20},
            ],
        )
        assert ctx.intent_winner == "composition"

    def test_ast_share_formula_is_composition(self) -> None:
        ctx = infer_intent(
            sql="SELECT categoria, SUM(monto)/SUM(SUM(monto)) OVER() AS share "
                "FROM ventas GROUP BY categoria",
            schema_defs=[("categoria", "VARCHAR"), ("monto", "DOUBLE")],
            data=[
                {"categoria": "A", "monto": 45000},
                {"categoria": "B", "monto": 35000},
                {"categoria": "C", "monto": 20000},
            ],
        )
        assert ctx.intent_winner == "composition"

    def test_rate_column_tasa_mora_is_comparison(self) -> None:
        ctx = infer_intent(
            sql="SELECT area, AVG(tasa_mora) AS mora FROM cartera GROUP BY area",
            schema_defs=[("area", "VARCHAR"), ("tasa_mora", "DOUBLE")],
            data=[
                {"area": "Norte", "tasa_mora": 0.12},
                {"area": "Sur",   "tasa_mora": 0.08},
                {"area": "Este",  "tasa_mora": 0.15},
            ],
        )
        assert ctx.intent_winner == "comparison"


class TestFunnelIntent:
    """§16.29 — funnel intent tests including is_monotonic_decreasing fix."""

    def test_case_when_funnel_d0(self) -> None:
        ctx = infer_intent(
            sql=(
                "SELECT CASE WHEN step = 1 THEN 'Visit' WHEN step = 2 THEN 'Signup' "
                "END AS stage, COUNT(*) FROM events GROUP BY 1"
            ),
        )
        assert ctx.intent_winner == "funnel"

    def test_monotonic_decreasing_funnel_d2(self) -> None:
        """§FASE_G: no CASE WHEN → comparison wins even with monotone data.
        Policy: CASE WHEN is required for funnel; monotone data alone is insufficient
        (would false-positive on age buckets, salary distributions, etc.)."""
        ctx = infer_intent(
            sql="SELECT step, COUNT(*) FROM events GROUP BY step ORDER BY MIN(step_order)",
            schema_defs=[("step", "VARCHAR"), ("count", "BIGINT")],
            data=[
                {"step": "Visit",    "count": 1000},
                {"step": "Signup",   "count": 600},
                {"step": "Activate", "count": 350},
                {"step": "Purchase", "count": 180},
                {"step": "Repeat",   "count": 90},
            ],
        )
        assert ctx.intent_winner == "comparison"

    def test_comparison_wins_no_case_when_order_by_desc(self) -> None:
        """§16.29 guard: no CASE WHEN + ORDER BY DESC → comparison, not funnel."""
        ctx = infer_intent(
            sql="SELECT stage, COUNT(*) AS cnt FROM pipeline GROUP BY stage ORDER BY COUNT(*) DESC",
            schema_defs=[("stage", "VARCHAR"), ("cnt", "BIGINT")],
            data=[
                {"stage": "Lead",     "cnt": 840},
                {"stage": "Qualify",  "cnt": 420},
                {"stage": "Propose",  "cnt": 210},
                {"stage": "Negotiate","cnt": 105},
                {"stage": "Close",    "cnt": 52},
            ],
        )
        assert ctx.intent_winner == "comparison"


class TestRetentionIntent:
    """§16.30 — retention intent tests including distinct_entity_count_over_time fix."""

    def test_distinct_entity_count_retention_d2(self) -> None:
        """§16.30: COUNT(DISTINCT user_id) in schema + temporal → retention, not trend."""
        ctx = infer_intent(
            sql="SELECT signup_month, COUNT(DISTINCT user_id) FROM activity GROUP BY signup_month",
            schema_defs=[("signup_month", "DATE"), ("user_id", "INTEGER")],
            data=[
                {"signup_month": f"2024-{i:02d}-01", "user_id_count": 1000 - i * 120}
                for i in range(1, 7)
            ],
        )
        assert ctx.intent_winner == "retention"
        assert ctx.intent_raw_score > 0.85

    def test_dau_no_customer_entity_is_trend(self) -> None:
        """§16.30 guard: COUNT(DISTINCT user_id) AS dau — user_id aggregated away → trend wins."""
        ctx = infer_intent(
            sql=(
                "SELECT fecha, COUNT(DISTINCT user_id) AS dau "
                "FROM events GROUP BY fecha ORDER BY fecha"
            ),
            schema_defs=[("fecha", "DATE"), ("dau", "BIGINT")],
            data=[
                {"fecha": f"2024-01-{i:02d}", "dau": 12000 + i * 200}
                for i in range(1, 6)
            ],
        )
        assert ctx.intent_winner == "trend"


class TestExplainability:

    def test_score_trace_present(self) -> None:
        ctx = infer_intent(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
        )
        assert "intent" in ctx.score_trace
        assert "trend" in ctx.score_trace["intent"]
        assert "raw_score" in ctx.score_trace["intent"]["trend"]

    def test_explanation_not_empty(self) -> None:
        ctx = infer_intent(
            sql="SELECT SUM(revenue) FROM sales",
            data=[{"revenue": 1000}],
            schema_defs=[("revenue", "DOUBLE")],
        )
        assert len(ctx.explanation) > 0
        assert all("signal" in e for e in ctx.explanation)
        assert all("contribution" in e for e in ctx.explanation)
