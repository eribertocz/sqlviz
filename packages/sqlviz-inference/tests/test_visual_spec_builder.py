"""Tests for VisualSpecBuilder / VisualSpec — V0.2 Fase 0."""
from __future__ import annotations

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.spec.visual_spec_builder import VisualSpecBuilder

builder = VisualSpecBuilder()

_DATE_SCHEMA = [
    ColumnSchema(name="month", type="DATE"),
    ColumnSchema(name="revenue", type="DOUBLE"),
]
_CAT_SCHEMA = [
    ColumnSchema(name="region", type="VARCHAR"),
    ColumnSchema(name="sales", type="DOUBLE"),
]
_PIE_DATA = [{"category": "A", "pct": 40}, {"category": "B", "pct": 60}]
_PIE_SCHEMA = [
    ColumnSchema(name="category", type="VARCHAR"),
    ColumnSchema(name="pct", type="DOUBLE"),
]
_SCATTER_SCHEMA = [
    ColumnSchema(name="height", type="DOUBLE"),
    ColumnSchema(name="weight", type="DOUBLE"),
]
_SCATTER_DATA = [{"height": 170.0, "weight": 65.0}]


class TestVisualSpecLine:

    def test_x_is_first_column(self) -> None:
        spec = builder.build("line", _DATE_SCHEMA, [])
        assert spec.x_field == "month"

    def test_y_is_last_column(self) -> None:
        spec = builder.build("line", _DATE_SCHEMA, [])
        assert spec.y_fields == ["revenue"]

    def test_orientation_vertical(self) -> None:
        spec = builder.build("line", _DATE_SCHEMA, [])
        assert spec.orientation == "vertical"

    def test_chart_type_preserved(self) -> None:
        spec = builder.build("line", _DATE_SCHEMA, [])
        assert spec.chart_type == "line"

    def test_no_stacking(self) -> None:
        spec = builder.build("line", _DATE_SCHEMA, [])
        assert spec.stack is False

    def test_tooltip_includes_both_fields(self) -> None:
        spec = builder.build("line", _DATE_SCHEMA, [])
        assert "month" in spec.tooltip_fields
        assert "revenue" in spec.tooltip_fields


class TestVisualSpecBar:

    def test_bar_vertical_orientation(self) -> None:
        spec = builder.build("bar", _CAT_SCHEMA, [])
        assert spec.orientation == "vertical"
        assert spec.x_field == "region"
        assert spec.y_fields == ["sales"]

    def test_bar_horizontal_orientation(self) -> None:
        spec = builder.build("bar_horizontal", _CAT_SCHEMA, [])
        assert spec.orientation == "horizontal"
        assert spec.x_field == "region"
        assert spec.y_fields == ["sales"]


class TestVisualSpecPie:

    def test_pie_x_is_label(self) -> None:
        spec = builder.build("pie", _PIE_SCHEMA, _PIE_DATA)
        assert spec.x_field == "category"

    def test_pie_y_is_value(self) -> None:
        spec = builder.build("pie", _PIE_SCHEMA, _PIE_DATA)
        assert spec.y_fields == ["pct"]

    def test_pie_orientation_none(self) -> None:
        spec = builder.build("pie", _PIE_SCHEMA, _PIE_DATA)
        assert spec.orientation == "none"


class TestVisualSpecScatter:

    def test_scatter_x_is_first_numeric(self) -> None:
        spec = builder.build("scatter", _SCATTER_SCHEMA, _SCATTER_DATA)
        assert spec.x_field == "height"

    def test_scatter_y_is_second_numeric(self) -> None:
        spec = builder.build("scatter", _SCATTER_SCHEMA, _SCATTER_DATA)
        assert spec.y_fields == ["weight"]

    def test_scatter_orientation_none(self) -> None:
        spec = builder.build("scatter", _SCATTER_SCHEMA, _SCATTER_DATA)
        assert spec.orientation == "none"

    def test_scatter_fallback_to_columns_when_no_numerics(self) -> None:
        schema = [
            ColumnSchema(name="a", type="VARCHAR"),
            ColumnSchema(name="b", type="VARCHAR"),
        ]
        spec = builder.build("scatter", schema, [{"a": "x", "b": "y"}])
        assert spec.x_field == "a"
        assert spec.y_fields == ["b"]

    def test_scatter_numeric_detected_from_data_when_no_schema(self) -> None:
        spec = builder.build("scatter", [], [{"height": 170.0, "weight": 65.0}])
        assert spec.x_field == "height"
        assert spec.y_fields == ["weight"]


class TestVisualSpecHistogram:

    def test_histogram_same_as_bar(self) -> None:
        spec = builder.build("histogram", _CAT_SCHEMA, [])
        assert spec.x_field == "region"
        assert spec.y_fields == ["sales"]
        assert spec.orientation == "vertical"


class TestVisualSpecKPI:

    def test_kpi_x_field_none(self) -> None:
        schema = [ColumnSchema(name="total", type="DOUBLE")]
        spec = builder.build("kpi", schema, [{"total": 42.0}])
        assert spec.x_field is None

    def test_kpi_y_is_numeric_col(self) -> None:
        schema = [ColumnSchema(name="total", type="DOUBLE")]
        spec = builder.build("kpi", schema, [{"total": 42.0}])
        assert "total" in spec.y_fields

    def test_kpi_orientation_none(self) -> None:
        schema = [ColumnSchema(name="total", type="DOUBLE")]
        spec = builder.build("kpi", schema, [{"total": 42.0}])
        assert spec.orientation == "none"


class TestVisualSpecTable:

    def test_table_x_field_none(self) -> None:
        spec = builder.build("table", _CAT_SCHEMA, [])
        assert spec.x_field is None

    def test_table_y_fields_is_all_columns(self) -> None:
        spec = builder.build("table", _CAT_SCHEMA, [])
        assert spec.y_fields == ["region", "sales"]

    def test_table_orientation_none(self) -> None:
        spec = builder.build("table", _CAT_SCHEMA, [])
        assert spec.orientation == "none"


class TestVisualSpecEdgeCases:

    def test_empty_schema_and_data(self) -> None:
        spec = builder.build("bar", [], [])
        assert spec.chart_type == "bar"
        assert spec.x_field is None
        assert spec.y_fields == []

    def test_single_column(self) -> None:
        schema = [ColumnSchema(name="value", type="DOUBLE")]
        spec = builder.build("bar", schema, [])
        assert spec.x_field == "value"
        assert spec.y_fields == ["value"]

    def test_defaults(self) -> None:
        spec = builder.build("bar", _CAT_SCHEMA, [])
        assert spec.color_field is None
        assert spec.stack is False
        assert spec.number_format == "default"
        assert spec.sort_order == "none"


class TestVisualSpecPipeline:
    """VisualSpec flows through the pipeline and into InferenceResult."""

    def test_pipeline_populates_visual_spec(self) -> None:
        from sqlviz_inference.context import RuntimeContext
        from sqlviz_inference.pipeline import RuntimePipeline

        pipeline = RuntimePipeline()
        ctx = RuntimeContext(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month",
            data=[{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)],
            schema=[
                ColumnSchema(name="month", type="DATE"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
        )
        ctx = pipeline.run(ctx)

        assert ctx.visual_spec is not None
        assert ctx.visual_spec.chart_type == "line"
        assert ctx.visual_spec.x_field == "month"
        assert ctx.visual_spec.y_fields == ["revenue"]

    def test_visual_spec_in_inference_result(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
            data=[{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)],
            schema=[
                ColumnSchema(name="month", type="DATE"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
        )
        assert result.visual_spec is not None
        assert result.visual_spec.chart_type == "line"
        assert result.visual_spec.x_field == "month"

    def test_visual_spec_kpi(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 99999.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert result.visual_spec is not None
        assert result.visual_spec.chart_type == "kpi"
        assert result.visual_spec.x_field is None

    def test_visual_spec_bar_horizontal(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql=(
                "SELECT region, SUM(sales) FROM t"
                " GROUP BY region ORDER BY SUM(sales) DESC LIMIT 10"
            ),
            data=[{"region": f"R{i}", "sales": (10 - i) * 1000} for i in range(10)],
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="sales", type="DOUBLE"),
            ],
        )
        assert result.visual_spec is not None
        assert result.visual_spec.orientation in ("vertical", "horizontal")

    def test_to_dict_includes_visual_spec(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 42.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        d = result.to_dict()
        assert "visual_spec" in d
        assert d["visual_spec"]["chart_type"] == "kpi"
        assert d["visual_spec"]["x_field"] is None

    def test_graceful_degradation_no_data(self) -> None:
        from sqlviz_inference import infer

        result = infer(sql="SELECT * FROM t")
        assert result.visual_spec is not None
