"""Parser module tests — DOC5 Section 4.5."""
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.parser.sql_parser import SQLParser

parser = SQLParser()


def make_context(sql: str) -> RuntimeContext:
    ctx = RuntimeContext(sql=sql)
    return parser.run(ctx)


class TestFingerprint:

    def test_kpi_single_sum(self) -> None:
        ctx = make_context("SELECT SUM(revenue) FROM sales")
        assert ctx.fingerprint == "SUM_KPI"

    def test_kpi_single_count(self) -> None:
        ctx = make_context("SELECT COUNT(*) FROM orders")
        assert ctx.fingerprint == "COUNT_KPI"

    def test_time_series(self) -> None:
        ctx = make_context(
            "SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month"
        )
        assert ctx.fingerprint == "TIME_SUM_GROUP1_ORDER_ASC"

    def test_ranking(self) -> None:
        ctx = make_context(
            "SELECT product, COUNT(*) FROM orders "
            "GROUP BY product ORDER BY 2 DESC LIMIT 10"
        )
        assert ctx.fingerprint == "COUNT_GROUP1_ORDER_DESC_LIMIT"

    def test_detail_query(self) -> None:
        ctx = make_context("SELECT id, name, email FROM users")
        assert ctx.fingerprint == "UNKNOWN"

    def test_window_function(self) -> None:
        ctx = make_context(
            "SELECT date, SUM(revenue) OVER (ORDER BY date) FROM sales"
        )
        assert "WINDOW" in ctx.fingerprint

    def test_spanish_temporal(self) -> None:
        ctx_en = make_context(
            "SELECT month, SUM(revenue) FROM sales GROUP BY month"
        )
        ctx_es = make_context(
            "SELECT mes, SUM(ventas) FROM ventas GROUP BY mes"
        )
        assert ctx_en.fingerprint == ctx_es.fingerprint


class TestSQLFeatures:

    def test_group_by_detected(self) -> None:
        ctx = make_context("SELECT cat, COUNT(*) FROM t GROUP BY cat")
        assert ctx.feature_vector[0] == 1.0

    def test_order_by_desc(self) -> None:
        ctx = make_context("SELECT cat, SUM(v) FROM t GROUP BY cat ORDER BY 2 DESC")
        assert ctx.feature_vector[1] == 1.0
        assert ctx.feature_vector[2] == 1.0

    def test_aggregation_sum(self) -> None:
        ctx = make_context("SELECT SUM(revenue) FROM sales")
        assert ctx.feature_vector[4] == 1.0
        assert ctx.feature_vector[5] == 1.0

    def test_invalid_sql_graceful(self) -> None:
        ctx = make_context("THIS IS NOT SQL !!!###")
        assert ctx.fingerprint == "UNKNOWN"
        assert ctx.feature_vector == [0.0] * 39
        assert len(ctx.errors) > 0
        assert ctx.chart_winner == "table"
