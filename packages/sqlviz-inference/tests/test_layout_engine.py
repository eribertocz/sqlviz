"""Layout Engine tests -- DOC5 Section 9.4."""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.chart.chart_engine import ChartEngine
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.features.feature_engine import FeatureEngine
from sqlviz_inference.intent.intent_engine import IntentEngine
from sqlviz_inference.layout.layout_engine import LayoutEngine
from sqlviz_inference.parser.sql_parser import SQLParser
from sqlviz_inference.semantic.semantic_engine import SemanticEngine

parser = SQLParser()
features = FeatureEngine()
semantic = SemanticEngine()
intent = IntentEngine()
chart = ChartEngine()
layout = LayoutEngine()


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
    ctx = layout.run(ctx)
    return ctx


class TestKPILayout:

    def test_kpi_is_small(self) -> None:
        ctx = full_infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
            schema_defs=[("total", "DOUBLE")],
        )
        if ctx.chart_winner == "kpi":
            assert ctx.col_span <= 4
            assert ctx.row_span == 1
            assert ctx.panel_height_px == 120

    def test_kpi_importance_is_high(self) -> None:
        ctx = full_infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
            schema_defs=[("total", "DOUBLE")],
        )
        if ctx.chart_winner == "kpi":
            assert ctx.layout_importance > 0.4


class TestLineLayout:

    def test_line_is_full_width_double_height(self) -> None:
        ctx = full_infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month",
            schema_defs=[("month", "DATE"), ("revenue", "DOUBLE")],
        )
        if ctx.chart_winner == "line":
            assert ctx.col_span == 12
            assert ctx.row_span == 2
            assert ctx.panel_height_px == 360


class TestTableLayout:

    def test_table_is_full_width_double_height(self) -> None:
        ctx = full_infer(
            sql="SELECT id, name, email, phone FROM customers",
            schema_defs=[
                ("id", "INTEGER"), ("name", "VARCHAR"),
                ("email", "VARCHAR"), ("phone", "VARCHAR"),
            ],
        )
        if ctx.chart_winner == "table":
            assert ctx.col_span == 12
            assert ctx.row_span >= 2

    def test_large_table_gets_extra_height(self) -> None:
        data: list[dict[str, object]] = [{"id": i, "name": f"Name{i}"} for i in range(150)]
        ctx = full_infer(
            sql="SELECT id, name FROM customers",
            data=data,
            schema_defs=[("id", "INTEGER"), ("name", "VARCHAR")],
        )
        if ctx.chart_winner == "table":
            assert ctx.row_span >= 2


class TestScatterLayout:

    def test_scatter_is_square(self) -> None:
        ctx = full_infer(
            sql="SELECT price, quantity FROM products",
            data=[{"price": p, "quantity": q}
                  for p, q in [(10, 100), (20, 80), (30, 60)]],
            schema_defs=[("price", "DOUBLE"), ("quantity", "INTEGER")],
        )
        if ctx.chart_winner == "scatter":
            assert ctx.col_span == 6
            assert ctx.row_span == 2


class TestValidRanges:

    def test_col_span_in_valid_range(self) -> None:
        ctx = full_infer(
            "SELECT a, b FROM t",
            schema_defs=[("a", "VARCHAR"), ("b", "VARCHAR")],
        )
        assert 1 <= ctx.col_span <= 12

    def test_row_span_in_valid_range(self) -> None:
        ctx = full_infer(
            "SELECT a FROM t",
            schema_defs=[("a", "VARCHAR")],
        )
        assert 1 <= ctx.row_span <= 3

    def test_importance_in_valid_range(self) -> None:
        ctx = full_infer(
            "SELECT SUM(x) FROM t",
            schema_defs=[("x", "DOUBLE")],
        )
        assert 0.0 <= ctx.layout_importance <= 1.0

    def test_panel_height_px_is_positive(self) -> None:
        ctx = full_infer(
            "SELECT a FROM t",
            schema_defs=[("a", "VARCHAR")],
        )
        assert ctx.panel_height_px > 0


class TestPanelHeights:
    """Verify pixel height per chart type (40px Grafana grid unit standard)."""

    def test_kpi_height(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("kpi", 0) == 120

    def test_line_height(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("line", 0) == 360

    def test_bar_height(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("bar", 0) == 360

    def test_pie_height(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("pie", 0) == 320

    def test_scatter_height(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("scatter", 0) == 440

    def test_histogram_height(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("histogram", 0) == 360

    def test_bar_horizontal_min(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("bar_horizontal", 0) == 280
        assert LayoutEngine._calculate_height("bar_horizontal", 1) == 280

    def test_bar_horizontal_dynamic(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("bar_horizontal", 6) == 360
        assert LayoutEngine._calculate_height("bar_horizontal", 10) == 520

    def test_bar_horizontal_max(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("bar_horizontal", 12) == 600
        assert LayoutEngine._calculate_height("bar_horizontal", 20) == 600

    def test_table_min(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("table", 0) == 280
        assert LayoutEngine._calculate_height("table", 3) == 280

    def test_table_dynamic(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("table", 5) == 280
        assert LayoutEngine._calculate_height("table", 8) == 400
        assert LayoutEngine._calculate_height("table", 10) == 480

    def test_table_max(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("table", 16) == 720
        assert LayoutEngine._calculate_height("table", 30) == 720

    def test_unknown_chart_fallback(self) -> None:
        from sqlviz_inference.layout.layout_engine import LayoutEngine
        assert LayoutEngine._calculate_height("combo_line_bar", 5) == 360
