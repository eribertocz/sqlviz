"""Title Engine tests -- DOC5 Section 11.4."""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.chart.chart_engine import ChartEngine
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.features.feature_engine import FeatureEngine
from sqlviz_inference.intent.intent_engine import IntentEngine
from sqlviz_inference.parser.sql_parser import SQLParser
from sqlviz_inference.semantic.semantic_engine import SemanticEngine
from sqlviz_inference.title.title_engine import TitleEngine

parser = SQLParser()
features = FeatureEngine()
semantic = SemanticEngine()
intent = IntentEngine()
chart = ChartEngine()
title = TitleEngine()


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
    ctx = title.run(ctx)
    return ctx


class TestKPITitles:

    def test_total_revenue(self) -> None:
        ctx = full_infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
            schema_defs=[("total", "DOUBLE")],
        )
        assert "Total" in ctx.title


class TestTrendTitles:

    def test_revenue_by_month(self) -> None:
        ctx = full_infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
            schema_defs=[("month", "DATE"), ("revenue", "DOUBLE")],
        )
        assert "Revenue" in ctx.title
        assert "month" in ctx.title.lower()


class TestRankingTitles:

    def test_top_n_products(self) -> None:
        ctx = full_infer(
            sql="SELECT product, SUM(revenue) FROM sales "
                "GROUP BY product ORDER BY 2 DESC LIMIT 10",
            schema_defs=[("product", "VARCHAR"), ("revenue", "DOUBLE")],
        )
        assert "Top 10" in ctx.title


class TestDetailTitles:

    def test_customer_detail(self) -> None:
        ctx = full_infer(
            sql="SELECT id, name, email FROM customers",
            schema_defs=[
                ("id", "INTEGER"), ("name", "VARCHAR"), ("email", "VARCHAR"),
            ],
        )
        assert "detail" in ctx.title.lower() or "results" in ctx.title.lower()


class TestTitleConfidence:

    def test_confidence_higher_with_semantic_metric(self) -> None:
        ctx = full_infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
            schema_defs=[("month", "DATE"), ("revenue", "DOUBLE")],
        )
        assert ctx.title_confidence >= 0.7

    def test_invalid_sql_empty_title(self) -> None:
        ctx = full_infer(sql="NOT VALID SQL ###")
        assert ctx.title == ""
        assert ctx.title_confidence == 0.0
