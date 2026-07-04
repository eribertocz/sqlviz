"""Chart Engine tests -- DOC5 Section 8.6."""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.chart.chart_engine import V0_CHARTS, ChartEngine
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.features.feature_engine import FeatureEngine
from sqlviz_inference.intent.intent_engine import IntentEngine
from sqlviz_inference.parser.sql_parser import SQLParser
from sqlviz_inference.semantic.semantic_engine import SemanticEngine

parser = SQLParser()
features = FeatureEngine()
semantic = SemanticEngine()
intent = IntentEngine()
chart = ChartEngine()


def full_infer(
    sql: str,
    data: list[dict[str, object]] | None = None,
    schema_defs: list[tuple[str, str]] | None = None,
) -> RuntimeContext:
    schema = [ColumnSchema(name=n, type=t) for n, t in (schema_defs or [])]
    ctx = RuntimeContext(sql=sql, data=data or [], schema=schema)
    ctx = parser.run(ctx)
    ctx = features.run(ctx)
    ctx = semantic.run(ctx)
    ctx = intent.run(ctx)
    ctx = chart.run(ctx)
    return ctx


class TestChartSelection:

    def test_kpi_single_value(self) -> None:
        ctx = full_infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
            schema_defs=[("total", "DOUBLE")],
        )
        assert ctx.chart_winner == "kpi"

    def test_line_time_series(self) -> None:
        ctx = full_infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month",
            data=[{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)],
            schema_defs=[("month", "DATE"), ("revenue", "DOUBLE")],
        )
        assert ctx.chart_winner == "line"

    def test_bar_category_comparison(self) -> None:
        # 4 categories: low_cardinality threshold (≤3) does not fire → comparison wins
        ctx = full_infer(
            sql="SELECT region, SUM(revenue) FROM sales GROUP BY region",
            data=[
                {"region": "North", "revenue": 45000},
                {"region": "South", "revenue": 32000},
                {"region": "East",  "revenue": 28000},
                {"region": "West",  "revenue": 19000},
            ],
            schema_defs=[("region", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        assert ctx.chart_winner in ("bar", "bar_horizontal")

    def test_bar_horizontal_ranking(self) -> None:
        ctx = full_infer(
            sql="SELECT product, SUM(rev) FROM sales "
                "GROUP BY product ORDER BY 2 DESC LIMIT 10",
            schema_defs=[("product", "VARCHAR"), ("rev", "DOUBLE")],
        )
        assert ctx.chart_winner == "bar_horizontal"

    def test_table_detail_query(self) -> None:
        ctx = full_infer(
            sql="SELECT id, name, email, phone FROM customers",
            schema_defs=[
                ("id", "INTEGER"), ("name", "VARCHAR"),
                ("email", "VARCHAR"), ("phone", "VARCHAR"),
            ],
        )
        assert ctx.chart_winner == "table"

    def test_scatter_two_numerics(self) -> None:
        ctx = full_infer(
            sql="SELECT price, quantity FROM products",
            data=[{"price": p, "quantity": q}
                  for p, q in [(10, 100), (20, 80), (30, 60), (40, 40)]],
            schema_defs=[("price", "DOUBLE"), ("quantity", "INTEGER")],
        )
        assert ctx.chart_winner == "scatter"


class TestPenalties:

    def test_pie_penalized_with_many_categories(self) -> None:
        data = [{"cat": f"Cat{i}", "val": i} for i in range(20)]
        ctx = full_infer(
            sql="SELECT cat, SUM(val) FROM t GROUP BY cat",
            data=data,
            schema_defs=[("cat", "VARCHAR"), ("val", "DOUBLE")],
        )
        assert ctx.chart_winner != "pie"

    def test_line_penalized_without_temporal(self) -> None:
        ctx = full_infer(
            sql="SELECT category, SUM(revenue) FROM sales GROUP BY category",
            schema_defs=[("category", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        assert ctx.chart_winner != "line"


class TestFallback:

    def test_fallback_applied_when_low_confidence(self) -> None:
        ctx = full_infer(
            sql="SELECT a, b, c FROM t WHERE x > 1",
            schema_defs=[("a", "VARCHAR"), ("b", "VARCHAR"), ("c", "VARCHAR")],
        )
        if ctx.fallback_applied:
            assert ctx.chart_winner == "table"
            assert ctx.fallback_reason != ""


class TestMultiMetricPenalty:
    """§16.24 — bar's has_two_numeric_columns penalty is intent-conditional."""

    def test_two_pure_numerics_without_group_by_is_scatter(self) -> None:
        # intent=correlation → bar penalty still applies → scatter wins
        ctx = full_infer(
            sql="SELECT revenue, cost FROM sales_data",
            schema_defs=[("revenue", "DOUBLE"), ("cost", "DOUBLE")],
            data=[
                {"revenue": 100, "cost": 80},
                {"revenue": 200, "cost": 150},
                {"revenue": 300, "cost": 220},
                {"revenue": 400, "cost": 310},
            ],
        )
        assert ctx.chart_winner == "scatter"

    def test_multi_metric_comparison_is_bar_not_pie(self) -> None:
        # intent=comparison with ≥2 numeric outputs → bar penalty suppressed → bar wins
        ctx = full_infer(
            sql="SELECT region, SUM(revenue) AS rev, SUM(cost) AS cost, "
                "AVG(margin_pct) AS margin FROM sales GROUP BY region",
            schema_defs=[
                ("region", "VARCHAR"),
                ("revenue", "DOUBLE"),
                ("cost", "DOUBLE"),
                ("margin_pct", "DOUBLE"),
            ],
            data=[
                {"region": "Norte", "rev": 450000, "cost": 280000, "margin": 0.38},
                {"region": "Sur",   "rev": 320000, "cost": 195000, "margin": 0.39},
                {"region": "Este",  "rev": 285000, "cost": 172000, "margin": 0.40},
                {"region": "Oeste", "rev": 198000, "cost": 124000, "margin": 0.37},
            ],
        )
        assert ctx.chart_winner in ("bar", "table")
        assert ctx.chart_winner != "scatter"
        assert ctx.chart_winner != "pie"


class TestExplainability:

    def test_score_trace_has_all_charts(self) -> None:
        ctx = full_infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
        )
        for chart_type in V0_CHARTS:
            assert chart_type in ctx.score_trace["chart"]

    def test_alternatives_present_when_close(self) -> None:
        ctx = full_infer(
            sql="SELECT region, SUM(revenue) FROM sales GROUP BY region",
            schema_defs=[("region", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        if ctx.chart_confidence_gap < 0.60:
            assert len(ctx.chart_alternatives) > 0
