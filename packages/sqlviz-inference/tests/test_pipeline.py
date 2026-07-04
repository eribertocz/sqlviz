"""Runtime Pipeline integration tests — DOC5 Section 12.7."""
from __future__ import annotations

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.pipeline import RuntimePipeline
from sqlviz_inference.result import InferenceResult

pipeline = RuntimePipeline()


class TestFullPipeline:

    def test_complete_trend_inference(self) -> None:
        ctx = RuntimeContext(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month",
            data=[{"month": f"2024-{i:02d}", "revenue": i * 1000} for i in range(1, 13)],
            schema=[
                ColumnSchema(name="month", type="DATE"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
        )
        ctx = pipeline.run(ctx)
        result = InferenceResult.from_context(ctx)

        assert result.intent_winner == "trend"
        assert result.chart_winner == "line"
        assert result.chart_quality == "high"
        assert result.fallback_applied is False
        assert result.col_span == 12
        assert "Revenue" in result.title
        assert result.fingerprint == "TIME_SUM_GROUP1_ORDER_ASC"
        # feature_vector has 39 dims (0-38 inclusive; dim 38 = trend_direction §16.5)
        assert len(result.feature_vector) == 39
        assert result.elapsed_ms < 1000  # under 1 second

    def test_complete_kpi_inference(self) -> None:
        ctx = RuntimeContext(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
        )
        ctx = pipeline.run(ctx)
        result = InferenceResult.from_context(ctx)

        assert result.chart_winner == "kpi"
        assert result.col_span <= 4

    def test_graceful_degradation_invalid_sql(self) -> None:
        ctx = RuntimeContext(sql="THIS IS NOT VALID SQL ###")
        ctx = pipeline.run(ctx)
        result = InferenceResult.from_context(ctx)

        # Pipeline must still produce a valid result
        assert result.chart_winner == "table"
        assert result.fingerprint == "UNKNOWN"
        assert len(result.errors) > 0
        assert result.col_span >= 1

    def test_filters_with_range_pairing(self) -> None:
        ctx = RuntimeContext(
            sql=(
                "SELECT region, SUM(revenue) FROM sales "
                "WHERE fecha >= $desde AND fecha <= $hasta "
                "GROUP BY region"
            ),
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="revenue", type="DOUBLE"),
                ColumnSchema(name="fecha", type="DATE"),
            ],
        )
        ctx = pipeline.run(ctx)
        result = InferenceResult.from_context(ctx)

        assert len(result.filter_controls) == 1
        assert result.filter_controls[0]["control_type"] == "date_range_picker"

    def test_score_trace_complete(self) -> None:
        ctx = RuntimeContext(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month"
        )
        ctx = pipeline.run(ctx)
        result = InferenceResult.from_context(ctx)

        assert "intent" in result.score_trace
        assert "chart" in result.score_trace
        assert "layout" in result.score_trace
        assert "semantic" in result.score_trace
        assert "pipeline" in result.score_trace

    def test_versioning_present(self) -> None:
        ctx = RuntimeContext(sql="SELECT SUM(x) FROM t")
        ctx = pipeline.run(ctx)
        result = InferenceResult.from_context(ctx)

        assert result.rules_version != ""
        assert result.feature_vector_version == "v0"
        assert result.engine_version != ""


class TestPublicInferFunction:
    """Test the top-level infer() public API."""

    def test_infer_trend(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month"
        )
        assert result.intent_winner == "trend"
        assert result.chart_winner == "line"

    def test_infer_kpi(self) -> None:
        from sqlviz_inference import infer

        result = infer(
            sql="SELECT SUM(revenue) AS total FROM sales",
            data=[{"total": 125430.0}],
        )
        assert result.chart_winner == "kpi"

    def test_infer_invalid_sql_does_not_raise(self) -> None:
        from sqlviz_inference import infer

        result = infer(sql="GARBAGE SQL !!!")
        assert result.chart_winner == "table"
        assert len(result.errors) > 0
