"""Tests for ResultProfiler / DataProfile — V0.2 Fase 0."""
from __future__ import annotations

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.profile.data_profile import ResultProfiler

profiler = ResultProfiler()


class TestResultProfilerBasic:

    def test_single_row_kpi(self) -> None:
        data = [{"total": 125430.0}]
        schema = [ColumnSchema(name="total", type="DOUBLE")]
        dp = profiler.build(data, schema)

        assert dp.row_count == 1
        assert dp.col_count == 1
        assert dp.single_row is True
        assert dp.wide_table is False
        assert len(dp.column_profiles) == 1

        col = dp.column_profiles[0]
        assert col.name == "total"
        assert col.is_numeric is True
        assert col.null_count == 0
        assert col.null_fraction == 0.0
        assert col.cardinality == 1

    def test_timeseries_12_rows(self) -> None:
        data = [{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)]
        schema = [
            ColumnSchema(name="month", type="DATE"),
            ColumnSchema(name="revenue", type="DOUBLE"),
        ]
        dp = profiler.build(data, schema)

        assert dp.row_count == 12
        assert dp.col_count == 2
        assert dp.single_row is False
        assert dp.wide_table is False

        month_col = dp.column_profiles[0]
        revenue_col = dp.column_profiles[1]

        assert month_col.name == "month"
        assert month_col.is_numeric is False
        assert month_col.cardinality == 12

        assert revenue_col.name == "revenue"
        assert revenue_col.is_numeric is True

    def test_wide_table_flag(self) -> None:
        data = [{f"col_{i}": i for i in range(7)} for _ in range(25)]
        schema = [ColumnSchema(name=f"col_{i}", type="INTEGER") for i in range(7)]
        dp = profiler.build(data, schema)

        assert dp.row_count == 25
        assert dp.col_count == 7
        assert dp.wide_table is True

    def test_not_wide_table_when_few_rows(self) -> None:
        data = [{f"col_{i}": i for i in range(7)} for _ in range(10)]
        schema = [ColumnSchema(name=f"col_{i}", type="INTEGER") for i in range(7)]
        dp = profiler.build(data, schema)

        assert dp.wide_table is False

    def test_null_handling(self) -> None:
        data = [
            {"region": "North", "sales": 100},
            {"region": None, "sales": 200},
            {"region": "South", "sales": None},
        ]
        schema = [
            ColumnSchema(name="region", type="VARCHAR"),
            ColumnSchema(name="sales", type="INTEGER"),
        ]
        dp = profiler.build(data, schema)

        region_col = dp.column_profiles[0]
        assert region_col.null_count == 1
        assert abs(region_col.null_fraction - 1 / 3) < 1e-9
        assert region_col.cardinality == 2  # "North", "South" — None excluded

        sales_col = dp.column_profiles[1]
        assert sales_col.null_count == 1

    def test_empty_data_no_schema(self) -> None:
        dp = profiler.build([], [])

        assert dp.row_count == 0
        assert dp.col_count == 0
        assert dp.single_row is False
        assert dp.wide_table is False
        assert dp.column_profiles == []

    def test_empty_data_with_schema(self) -> None:
        schema = [ColumnSchema(name="x", type="INTEGER")]
        dp = profiler.build([], schema)

        assert dp.row_count == 0
        assert dp.col_count == 1
        assert len(dp.column_profiles) == 1
        assert dp.column_profiles[0].cardinality == 0
        assert dp.column_profiles[0].null_count == 0
        assert dp.column_profiles[0].max_label_length == 0
        assert dp.column_profiles[0].mean_label_length == 0.0

    def test_max_and_mean_label_length(self) -> None:
        data = [
            {"category": "A"},
            {"category": "Long Label"},
            {"category": "Med"},
        ]
        schema = [ColumnSchema(name="category", type="VARCHAR")]
        dp = profiler.build(data, schema)

        col = dp.column_profiles[0]
        assert col.max_label_length == len("Long Label")
        assert abs(col.mean_label_length - (1 + 10 + 3) / 3) < 1e-9

    def test_no_schema_infers_from_data(self) -> None:
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        dp = profiler.build(data, [])

        assert dp.row_count == 2
        assert dp.col_count == 2

    def test_numeric_type_detection(self) -> None:
        numeric_types = ["TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
                         "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL"]
        for t in numeric_types:
            schema = [ColumnSchema(name="x", type=t)]
            dp = profiler.build([{"x": 1}], schema)
            assert dp.column_profiles[0].is_numeric is True, f"{t} should be numeric"

    def test_non_numeric_types(self) -> None:
        for t in ["VARCHAR", "TEXT", "DATE", "TIMESTAMP", "BOOLEAN"]:
            schema = [ColumnSchema(name="x", type=t)]
            dp = profiler.build([{"x": "val"}], schema)
            assert dp.column_profiles[0].is_numeric is False, f"{t} should not be numeric"

    def test_decimal_type_with_precision(self) -> None:
        schema = [ColumnSchema(name="price", type="DECIMAL(10,2)")]
        dp = profiler.build([{"price": 9.99}], schema)
        assert dp.column_profiles[0].is_numeric is True


class TestResultProfilerPipeline:
    """DataProfile surfaces in the pipeline via RuntimeContext."""

    def test_pipeline_populates_data_profile(self) -> None:
        from sqlviz_inference.context import RuntimeContext
        from sqlviz_inference.pipeline import RuntimePipeline

        pipeline = RuntimePipeline()
        ctx = RuntimeContext(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
            data=[{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)],
            schema=[
                ColumnSchema(name="month", type="DATE"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
        )
        ctx = pipeline.run(ctx)

        assert ctx.data_profile is not None
        assert ctx.data_profile.row_count == 12
        assert ctx.data_profile.col_count == 2

    def test_data_profile_in_inference_result(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT region, SUM(sales) FROM t GROUP BY region",
            data=[{"region": "North", "sales": 1000}, {"region": "South", "sales": 2000}],
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="sales", type="DOUBLE"),
            ],
        )
        assert result.data_profile is not None
        assert result.data_profile.row_count == 2
        assert result.data_profile.single_row is False

    def test_data_profile_kpi_single_row(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 99999.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        assert result.data_profile is not None
        assert result.data_profile.single_row is True
        assert result.data_profile.col_count == 1

    def test_graceful_degradation_no_data(self) -> None:
        from sqlviz_inference import infer

        result = infer(sql="SELECT * FROM t")
        assert result.data_profile is not None
        assert result.data_profile.row_count == 0

    def test_to_dict_includes_data_profile(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 42.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        d = result.to_dict()
        assert "data_profile" in d
        assert d["data_profile"]["row_count"] == 1
        assert d["data_profile"]["single_row"] is True
