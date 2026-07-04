"""Feature Engine tests — DOC5 Sections 5.9 and 16.2."""
from typing import Any

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.features.feature_engine import FeatureEngine

engine = FeatureEngine()


def make_context(
    data: list[dict[str, Any]],
    schema_defs: list[tuple[str, str]],
) -> RuntimeContext:
    schema = [ColumnSchema(name=n, type=t) for n, t in schema_defs]
    ctx = RuntimeContext(sql="SELECT 1", data=data, schema=schema)
    return engine.run(ctx)


class TestColumnFeatures:

    def test_date_column_detected(self) -> None:
        ctx = make_context(
            data=[{"month": "2024-01", "revenue": 1000}],
            schema_defs=[("month", "DATE"), ("revenue", "DOUBLE")],
        )
        assert ctx.feature_vector[18] == 1.0  # has_date_column
        assert ctx.feature_vector[19] == 1.0  # has_numeric_column

    def test_single_numeric_kpi_signal(self) -> None:
        ctx = make_context(
            data=[{"total": 125430}],
            schema_defs=[("total", "DOUBLE")],
        )
        assert ctx.feature_vector[23] == 1.0  # has_single_numeric_column


class TestResultShape:

    def test_kpi_shape_detected(self) -> None:
        ctx = make_context(
            data=[{"total": 125430}],
            schema_defs=[("total", "DOUBLE")],
        )
        assert ctx.feature_vector[35] == 1.0  # result_row_count_is_1
        assert ctx.feature_vector[36] == 1.0  # result_column_count_is_1

    def test_wide_table_detected(self) -> None:
        row = {f"col{i}": i for i in range(8)}
        data = [row] * 25
        schema_defs = [(f"col{i}", "INTEGER") for i in range(8)]
        ctx = make_context(data=data, schema_defs=schema_defs)
        assert ctx.feature_vector[37] == 1.0  # result_is_wide_table


class TestDataStatistics:

    def test_trend_strength_strong(self) -> None:
        data = [{"month": i, "revenue": i * 1000} for i in range(1, 13)]
        schema_defs = [("month", "INTEGER"), ("revenue", "DOUBLE")]
        ctx = make_context(data=data, schema_defs=schema_defs)
        assert ctx.feature_vector[28] > 0.90  # strong R²

    def test_row_count_normalized(self) -> None:
        data = [{"x": i} for i in range(5000)]
        schema_defs = [("x", "INTEGER")]
        ctx = make_context(data=data, schema_defs=schema_defs)
        assert ctx.feature_vector[25] == 0.5  # 5000/10000


class TestTrendDirection:

    def test_growing_trend_direction_high(self) -> None:
        data = [{"month": i, "revenue": i * 1000} for i in range(1, 13)]
        schema_defs = [("month", "INTEGER"), ("revenue", "DOUBLE")]
        ctx = make_context(data=data, schema_defs=schema_defs)
        assert ctx.feature_vector[38] > 0.65  # clearly growing

    def test_declining_trend_direction_low(self) -> None:
        data = [{"month": i, "revenue": (13 - i) * 1000} for i in range(1, 13)]
        schema_defs = [("month", "INTEGER"), ("revenue", "DOUBLE")]
        ctx = make_context(data=data, schema_defs=schema_defs)
        assert ctx.feature_vector[38] < 0.35  # clearly declining

    def test_flat_trend_direction_neutral(self) -> None:
        data = [{"month": i, "revenue": 5000} for i in range(1, 13)]
        schema_defs = [("month", "INTEGER"), ("revenue", "DOUBLE")]
        ctx = make_context(data=data, schema_defs=schema_defs)
        assert 0.35 <= ctx.feature_vector[38] <= 0.65

    def test_strength_and_direction_are_independent(self) -> None:
        growing = [{"month": i, "revenue": i * 1000} for i in range(1, 13)]
        declining = [
            {"month": i, "revenue": (13 - i) * 1000} for i in range(1, 13)
        ]
        schema_defs = [("month", "INTEGER"), ("revenue", "DOUBLE")]

        ctx_g = make_context(data=growing, schema_defs=schema_defs)
        ctx_d = make_context(data=declining, schema_defs=schema_defs)

        assert abs(ctx_g.feature_vector[28] - ctx_d.feature_vector[28]) < 0.05
        assert ctx_g.feature_vector[38] > 0.65
        assert ctx_d.feature_vector[38] < 0.35
