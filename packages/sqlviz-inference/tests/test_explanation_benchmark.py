"""Explanation benchmark — validates ExplanationEngine V2 on gold cases (DOC10 Fase F).

Each case checks:
- explanation_v2 is not None
- chart_winner matches expected
- reason_main is non-empty
- full_text is non-empty and starts with "Elegí"
"""
from __future__ import annotations

import pytest
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.pipeline import RuntimePipeline

pipeline = RuntimePipeline()


GOLD_CASES: list[dict] = [
    # ── trend ───────────────────────────────────────────────────────────────
    {
        "id": "trend_line_monthly_revenue",
        "sql": "SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month",
        "schema": [
            {"name": "month", "type": "DATE"},
            {"name": "revenue", "type": "DOUBLE"},
        ],
        "expected_chart": "line",
        "expected_intent": "trend",
    },
    {
        "id": "trend_bar_quarterly",
        "sql": "SELECT quarter, total FROM summary ORDER BY quarter",
        "schema": [
            {"name": "quarter", "type": "VARCHAR"},
            {"name": "total", "type": "DOUBLE"},
        ],
        "data": [
            {"quarter": "Q1", "total": 100.0},
            {"quarter": "Q2", "total": 120.0},
            {"quarter": "Q3", "total": 90.0},
        ],
        "expected_intent": "trend",
    },
    # ── comparison ──────────────────────────────────────────────────────────
    {
        "id": "comparison_bar_category_sales",
        "sql": "SELECT category, SUM(sales) FROM products GROUP BY category",
        "schema": [
            {"name": "category", "type": "VARCHAR"},
            {"name": "sales", "type": "DOUBLE"},
        ],
        "data": [
            {"category": "A", "sales": 200.0},
            {"category": "B", "sales": 150.0},
            {"category": "C", "sales": 300.0},
        ],
        "expected_intent": "comparison",
    },
    {
        "id": "comparison_bar_horizontal_long_labels",
        "sql": (
            "SELECT product_name, SUM(units_sold) AS units "
            "FROM orders GROUP BY product_name ORDER BY units DESC"
        ),
        "schema": [
            {"name": "product_name", "type": "VARCHAR"},
            {"name": "units", "type": "INTEGER"},
        ],
        "data": [
            {"product_name": "Wireless Bluetooth Headphones Pro", "units": 500},
            {"product_name": "Ultra HD 4K Smart Television 55in", "units": 320},
            {"product_name": "Gaming Mechanical Keyboard RGB", "units": 410},
            {"product_name": "Portable Solar Charging Station", "units": 280},
            {"product_name": "Professional Coffee Maker Deluxe", "units": 190},
            {"product_name": "Smart Home Security Camera Kit", "units": 390},
        ],
        "expected_intent": "comparison",
    },
    # ── ranking ─────────────────────────────────────────────────────────────
    {
        "id": "ranking_bar_horizontal_top10",
        "sql": "SELECT name, revenue FROM reps ORDER BY revenue DESC LIMIT 10",
        "schema": [
            {"name": "name", "type": "VARCHAR"},
            {"name": "revenue", "type": "DOUBLE"},
        ],
        "data": [{"name": f"Rep {i}", "revenue": float(1000 - i * 80)} for i in range(10)],
        "expected_chart": "bar_horizontal",
        "expected_intent": "ranking",
    },
    {
        "id": "ranking_bar_top5_short_labels",
        "sql": "SELECT dept, score FROM depts ORDER BY score DESC LIMIT 5",
        "schema": [
            {"name": "dept", "type": "VARCHAR"},
            {"name": "score", "type": "DOUBLE"},
        ],
        "data": [{"dept": f"D{i}", "score": float(100 - i * 10)} for i in range(5)],
        "expected_intent": "ranking",
    },
    # ── composition ─────────────────────────────────────────────────────────
    {
        "id": "composition_pie_few_slices",
        "sql": "SELECT region, SUM(revenue) FROM sales GROUP BY region",
        "schema": [
            {"name": "region", "type": "VARCHAR"},
            {"name": "revenue", "type": "DOUBLE"},
        ],
        "data": [
            {"region": "North", "revenue": 400.0},
            {"region": "South", "revenue": 250.0},
            {"region": "East", "revenue": 350.0},
        ],
        "expected_chart": "pie",
        "expected_intent": "composition",
    },
    # ── distribution ────────────────────────────────────────────────────────
    {
        "id": "distribution_histogram_age",
        "sql": "SELECT age FROM users",
        "schema": [{"name": "age", "type": "INTEGER"}],
        "data": [{"age": 20 + i} for i in range(50)],
        "expected_chart": "histogram",
        "expected_intent": "distribution",
    },
    # ── correlation ─────────────────────────────────────────────────────────
    {
        "id": "correlation_scatter_two_metrics",
        "sql": "SELECT marketing_spend, revenue FROM campaigns",
        "schema": [
            {"name": "marketing_spend", "type": "DOUBLE"},
            {"name": "revenue", "type": "DOUBLE"},
        ],
        "data": [
            {"marketing_spend": float(i * 10), "revenue": float(i * 25 + 50)}
            for i in range(20)
        ],
        "expected_chart": "scatter",
        "expected_intent": "correlation",
    },
    # ── kpi ─────────────────────────────────────────────────────────────────
    {
        "id": "kpi_total_revenue",
        "sql": "SELECT SUM(revenue) AS total_revenue FROM orders",
        "schema": [{"name": "total_revenue", "type": "DOUBLE"}],
        "data": [{"total_revenue": 125000.0}],
        "expected_chart": "kpi",
        "expected_intent": "kpi",
    },
    {
        "id": "kpi_count",
        "sql": "SELECT COUNT(*) AS total_users FROM users",
        "schema": [{"name": "total_users", "type": "INTEGER"}],
        "data": [{"total_users": 3200}],
        "expected_chart": "kpi",
        "expected_intent": "kpi",
    },
    # ── detail ──────────────────────────────────────────────────────────────
    {
        "id": "detail_table_full_data",
        "sql": "SELECT id, name, email, status, created_at FROM users LIMIT 100",
        "schema": [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"},
            {"name": "email", "type": "VARCHAR"},
            {"name": "status", "type": "VARCHAR"},
            {"name": "created_at", "type": "TIMESTAMP"},
        ],
        "data": [
            {
                "id": i, "name": f"User{i}", "email": f"u{i}@x.com",
                "status": "active", "created_at": "2024-01-01",
            }
            for i in range(20)
        ],
        "expected_chart": "table",
        "expected_intent": "detail",
    },
    # ── additional trend/comparison to reach 30 assertions ──────────────────
    {
        "id": "trend_line_daily",
        "sql": "SELECT day, clicks FROM ad_data ORDER BY day",
        "schema": [
            {"name": "day", "type": "DATE"},
            {"name": "clicks", "type": "INTEGER"},
        ],
        "expected_intent": "trend",
    },
    {
        "id": "kpi_avg",
        "sql": "SELECT AVG(price) AS avg_price FROM products",
        "schema": [{"name": "avg_price", "type": "DOUBLE"}],
        "data": [{"avg_price": 49.99}],
        "expected_chart": "kpi",
        "expected_intent": "kpi",
    },
    {
        "id": "comparison_bar_two_categories",
        "sql": "SELECT plan, COUNT(*) AS users FROM subscriptions GROUP BY plan",
        "schema": [
            {"name": "plan", "type": "VARCHAR"},
            {"name": "users", "type": "INTEGER"},
        ],
        "data": [
            {"plan": "free", "users": 800},
            {"plan": "pro", "users": 200},
        ],
        "expected_intent": "comparison",
    },
]


def _run(case: dict) -> RuntimeContext:
    schema = [ColumnSchema(name=c["name"], type=c["type"]) for c in case.get("schema", [])]
    ctx = RuntimeContext(
        sql=case["sql"],
        data=case.get("data") or [],
        schema=schema,
    )
    return pipeline.run(ctx)


@pytest.mark.parametrize("case", GOLD_CASES, ids=[c["id"] for c in GOLD_CASES])
def test_explanation_v2_not_none(case: dict) -> None:
    ctx = _run(case)
    assert ctx.explanation_v2 is not None, f"[{case['id']}] explanation_v2 is None"


@pytest.mark.parametrize("case", GOLD_CASES, ids=[c["id"] for c in GOLD_CASES])
def test_explanation_reason_main_non_empty(case: dict) -> None:
    ctx = _run(case)
    assert ctx.explanation_v2 is not None
    assert len(ctx.explanation_v2.reason_main) > 0, f"[{case['id']}] reason_main is empty"


@pytest.mark.parametrize("case", GOLD_CASES, ids=[c["id"] for c in GOLD_CASES])
def test_explanation_full_text_non_empty(case: dict) -> None:
    ctx = _run(case)
    assert ctx.explanation_v2 is not None
    assert len(ctx.explanation_v2.full_text) > 0, f"[{case['id']}] full_text is empty"


@pytest.mark.parametrize("case", GOLD_CASES, ids=[c["id"] for c in GOLD_CASES])
def test_explanation_full_text_format(case: dict) -> None:
    ctx = _run(case)
    assert ctx.explanation_v2 is not None
    assert ctx.explanation_v2.full_text.startswith("Elegí"), (
        f"[{case['id']}] full_text does not start with 'Elegí': {ctx.explanation_v2.full_text[:80]}"
    )


@pytest.mark.parametrize("case", GOLD_CASES, ids=[c["id"] for c in GOLD_CASES])
def test_explanation_chart_winner_matches_context(case: dict) -> None:
    ctx = _run(case)
    assert ctx.explanation_v2 is not None
    assert ctx.explanation_v2.chart_winner == ctx.chart_winner, (
        f"[{case['id']}] explanation_v2.chart_winner={ctx.explanation_v2.chart_winner} "
        f"!= context.chart_winner={ctx.chart_winner}"
    )


@pytest.mark.parametrize("case", [c for c in GOLD_CASES if "expected_chart" in c],
                         ids=[c["id"] for c in GOLD_CASES if "expected_chart" in c])
def test_explanation_chart_winner_matches_expected(case: dict) -> None:
    ctx = _run(case)
    assert ctx.explanation_v2 is not None
    assert ctx.explanation_v2.chart_winner == case["expected_chart"], (
        f"[{case['id']}] expected {case['expected_chart']}, "
        f"got {ctx.explanation_v2.chart_winner}"
    )
