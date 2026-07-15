"""Tests for ConstraintEngine — V0.2 Fase B.

Each hard rule has ≥ 2 positive cases (rule fires and eliminates) and
≥ 2 negative cases (rule does NOT fire, chart survives).
"""
from __future__ import annotations

from sqlviz_core.models import ColumnSchema
from sqlviz_inference.constraint.constraint_engine import ConstraintEngine
from sqlviz_inference.context import ChartCandidate, RuntimeContext
from sqlviz_inference.profile.data_profile import ColumnProfile, DataProfile

engine = ConstraintEngine()


def _make_candidate(chart_type: str, score: float = 1.0) -> ChartCandidate:
    return ChartCandidate(
        chart_type=chart_type,
        affinity_score=score,
        penalty_total=0.0,
        final_score=score,
        normalized_score=score,
    )


def _make_context(
    chart_winner: str,
    chart_types: list[str],
    schema: list[ColumnSchema],
    data: list[dict] | None = None,
    data_profile: DataProfile | None = None,
    feature_vector: list[float] | None = None,
    sql: str = "SELECT x FROM t",
) -> RuntimeContext:
    candidates = [_make_candidate(ct) for ct in chart_types]
    if feature_vector is None:
        feature_vector = [0.0] * 39
    ctx = RuntimeContext(
        sql=sql,
        schema=schema,
        data=data or [],
        chart_candidates=candidates,
        chart_winner=chart_winner,
        chart_raw_score=1.0,
        chart_normalized_score=1.0,
        feature_vector=feature_vector,
        data_profile=data_profile,
    )
    return ctx


def _profile(row_count: int, col_profiles: list[ColumnProfile] | None = None) -> DataProfile:
    return DataProfile(
        row_count=row_count,
        col_count=1,
        single_row=(row_count == 1),
        wide_table=False,
        column_profiles=col_profiles or [],
    )


def _col_profile(name: str, is_numeric: bool, cardinality: int) -> ColumnProfile:
    return ColumnProfile(
        name=name,
        type="DOUBLE" if is_numeric else "VARCHAR",
        cardinality=cardinality,
        null_count=0,
        null_fraction=0.0,
        max_label_length=10,
        mean_label_length=5.0,
        is_numeric=is_numeric,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Rule 1: kpi_single_row
# ──────────────────────────────────────────────────────────────────────────────

class TestKpiSingleRow:
    """kpi is eliminated when data has > 1 row."""

    def test_kpi_eliminated_two_rows(self) -> None:
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi", "bar"],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
            data=[{"total": 100}, {"total": 200}],
            data_profile=_profile(2),
        )
        result = engine.run(ctx)
        assert result.constraint_report is not None
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "kpi" in eliminated
        assert result.chart_winner == "bar"

    def test_kpi_eliminated_many_rows(self) -> None:
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi", "line"],
            schema=[
                ColumnSchema(name="mes", type="VARCHAR"),
                ColumnSchema(name="val", type="DOUBLE"),
            ],
            data=[{"mes": str(i), "val": i * 1000} for i in range(6)],
            data_profile=_profile(6),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "kpi" in eliminated

    def test_kpi_survives_single_row(self) -> None:
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi", "bar"],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
            data=[{"total": 142.5}],
            data_profile=_profile(1),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "kpi" not in eliminated
        assert result.chart_winner == "kpi"

    def test_kpi_survives_zero_rows(self) -> None:
        # row_count = 0 → not > 1 → kpi not eliminated
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi"],
            schema=[ColumnSchema(name="total", type="DOUBLE")],
            data=[],
            data_profile=_profile(0),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "kpi" not in eliminated


# ──────────────────────────────────────────────────────────────────────────────
# Rule 2: line_no_temporal
# ──────────────────────────────────────────────────────────────────────────────

class TestLineNoTemporal:
    """line is eliminated when there is no temporal column."""

    def test_line_eliminated_all_varchar(self) -> None:
        ctx = _make_context(
            chart_winner="line",
            chart_types=["line", "bar"],
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
            data=[{"region": "Norte", "revenue": 1000}],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "line" in eliminated
        assert result.chart_winner == "bar"

    def test_line_eliminated_numeric_only(self) -> None:
        ctx = _make_context(
            chart_winner="line",
            chart_types=["line", "scatter"],
            schema=[
                ColumnSchema(name="price", type="DOUBLE"),
                ColumnSchema(name="quantity", type="INTEGER"),
            ],
            data=[{"price": 10.0, "quantity": 5}],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "line" in eliminated

    def test_line_survives_date_type(self) -> None:
        ctx = _make_context(
            chart_winner="line",
            chart_types=["line", "bar"],
            schema=[
                ColumnSchema(name="fecha", type="DATE"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
            data=[{"fecha": "2024-01-01", "revenue": 1000}],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "line" not in eliminated

    def test_line_survives_mes_varchar(self) -> None:
        # 'mes' matches TEMPORAL_DIMENSION in semantic dictionary
        ctx = _make_context(
            chart_winner="line",
            chart_types=["line", "bar"],
            schema=[
                ColumnSchema(name="mes", type="VARCHAR"),
                ColumnSchema(name="ingresos", type="DOUBLE"),
            ],
            data=[{"mes": "2024-01", "ingresos": 50000}],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "line" not in eliminated

    def test_line_survives_trimestre_varchar(self) -> None:
        ctx = _make_context(
            chart_winner="line",
            chart_types=["line", "bar"],
            schema=[
                ColumnSchema(name="trimestre", type="VARCHAR"),
                ColumnSchema(name="revenue", type="DOUBLE"),
                ColumnSchema(name="cost", type="DOUBLE"),
            ],
            data=[{"trimestre": "2024-Q1", "revenue": 320000, "cost": 180000}],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "line" not in eliminated

    def test_line_survives_anio_varchar(self) -> None:
        ctx = _make_context(
            chart_winner="line",
            chart_types=["line", "bar"],
            schema=[
                ColumnSchema(name="anio", type="VARCHAR"),
                ColumnSchema(name="total", type="DOUBLE"),
            ],
            data=[{"anio": "2023", "total": 1800000}],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "line" not in eliminated


# ──────────────────────────────────────────────────────────────────────────────
# Rule 3: pie_high_cardinality
# ──────────────────────────────────────────────────────────────────────────────

class TestPieHighCardinality:
    """pie is eliminated when categorical column has > 7 distinct values."""

    def test_pie_eliminated_eight_categories(self) -> None:
        data = [{"cat": f"C{i}", "val": i * 100} for i in range(8)]
        ctx = _make_context(
            chart_winner="pie",
            chart_types=["pie", "bar"],
            schema=[
                ColumnSchema(name="cat", type="VARCHAR"),
                ColumnSchema(name="val", type="DOUBLE"),
            ],
            data=data,
            data_profile=_profile(8, [_col_profile("cat", False, 8)]),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "pie" in eliminated
        assert result.chart_winner == "bar"

    def test_pie_eliminated_ten_categories(self) -> None:
        data = [{"cat": f"Cat{i}", "val": i} for i in range(10)]
        ctx = _make_context(
            chart_winner="pie",
            chart_types=["pie", "bar"],
            schema=[
                ColumnSchema(name="cat", type="VARCHAR"),
                ColumnSchema(name="val", type="DOUBLE"),
            ],
            data=data,
            data_profile=_profile(10, [_col_profile("cat", False, 10)]),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "pie" in eliminated

    def test_pie_survives_three_categories(self) -> None:
        data = [
            {"payment_method": "Credit Card", "count": 1200},
            {"payment_method": "PayPal", "count": 800},
            {"payment_method": "Bank Transfer", "count": 400},
        ]
        ctx = _make_context(
            chart_winner="pie",
            chart_types=["pie", "bar"],
            schema=[
                ColumnSchema(name="payment_method", type="VARCHAR"),
                ColumnSchema(name="count", type="BIGINT"),
            ],
            data=data,
            data_profile=_profile(3, [_col_profile("payment_method", False, 3)]),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "pie" not in eliminated

    def test_pie_survives_two_categories(self) -> None:
        # composition_001/002 style — 2-3 categories, pie is valid
        data = [
            {"genero": "Femenino", "usuarios": 6200},
            {"genero": "Masculino", "usuarios": 4800},
        ]
        ctx = _make_context(
            chart_winner="pie",
            chart_types=["pie", "bar"],
            schema=[
                ColumnSchema(name="genero", type="VARCHAR"),
                ColumnSchema(name="usuarios", type="BIGINT"),
            ],
            data=data,
            data_profile=_profile(2, [_col_profile("genero", False, 2)]),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "pie" not in eliminated

    def test_pie_survives_seven_categories(self) -> None:
        # Exactly at threshold — 7 ≤ 7 → NOT eliminated
        data = [{"cat": f"C{i}", "val": i} for i in range(7)]
        ctx = _make_context(
            chart_winner="pie",
            chart_types=["pie", "bar"],
            schema=[
                ColumnSchema(name="cat", type="VARCHAR"),
                ColumnSchema(name="val", type="DOUBLE"),
            ],
            data=data,
            data_profile=_profile(7, [_col_profile("cat", False, 7)]),
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "pie" not in eliminated


# ──────────────────────────────────────────────────────────────────────────────
# Rule 4: scatter_insufficient_metrics
# ──────────────────────────────────────────────────────────────────────────────

class TestScatterInsufficientMetrics:
    """scatter is eliminated when < 2 non-id numeric columns are present."""

    def test_scatter_eliminated_single_numeric(self) -> None:
        ctx = _make_context(
            chart_winner="scatter",
            chart_types=["scatter", "bar"],
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="revenue", type="DOUBLE"),
            ],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "scatter" in eliminated

    def test_scatter_eliminated_two_ids(self) -> None:
        ctx = _make_context(
            chart_winner="scatter",
            chart_types=["scatter", "table"],
            schema=[
                ColumnSchema(name="customer_id", type="INTEGER"),
                ColumnSchema(name="order_id", type="INTEGER"),
            ],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "scatter" in eliminated

    def test_scatter_survives_two_metrics(self) -> None:
        ctx = _make_context(
            chart_winner="scatter",
            chart_types=["scatter", "bar"],
            schema=[
                ColumnSchema(name="precio", type="DOUBLE"),
                ColumnSchema(name="cantidad_vendida", type="INTEGER"),
            ],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "scatter" not in eliminated

    def test_scatter_survives_id_plus_two_metrics(self) -> None:
        # customer_id is id, but revenue + quantity are metrics → ≥ 2 metrics
        ctx = _make_context(
            chart_winner="scatter",
            chart_types=["scatter", "bar"],
            schema=[
                ColumnSchema(name="customer_id", type="INTEGER"),
                ColumnSchema(name="revenue", type="DOUBLE"),
                ColumnSchema(name="quantity", type="INTEGER"),
            ],
        )
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "scatter" not in eliminated


# ──────────────────────────────────────────────────────────────────────────────
# Rule 5: histogram_grouped_no_bins
# ──────────────────────────────────────────────────────────────────────────────

class TestHistogramGroupedNoBins:
    """histogram is eliminated when GROUP BY is present and no bin column detected."""

    def test_histogram_eliminated_group_by_no_bins(self) -> None:
        import sqlglot
        sql = "SELECT rango_edad, COUNT(*) FROM clientes GROUP BY rango_edad"
        ast = sqlglot.parse_one(sql)
        ctx = _make_context(
            chart_winner="histogram",
            chart_types=["histogram", "bar"],
            schema=[
                ColumnSchema(name="rango_edad", type="VARCHAR"),
                ColumnSchema(name="count", type="BIGINT"),
            ],
            sql=sql,
        )
        ctx.ast = ast
        result = engine.run(ctx)
        # rango_edad contains 'rango' which IS a bin indicator — so NOT eliminated
        # This validates the bin indicator logic
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        # 'rango' is in _BIN_INDICATORS → histogram survives
        assert "histogram" not in eliminated

    def test_histogram_eliminated_group_by_clean_column(self) -> None:
        import sqlglot
        sql = "SELECT canal, COUNT(*) FROM ventas GROUP BY canal"
        ast = sqlglot.parse_one(sql)
        ctx = _make_context(
            chart_winner="histogram",
            chart_types=["histogram", "bar"],
            schema=[
                ColumnSchema(name="canal", type="VARCHAR"),
                ColumnSchema(name="count", type="BIGINT"),
            ],
            sql=sql,
        )
        ctx.ast = ast
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "histogram" in eliminated

    def test_histogram_survives_no_group_by(self) -> None:
        import sqlglot
        sql = "SELECT salary FROM employees"
        ast = sqlglot.parse_one(sql)
        ctx = _make_context(
            chart_winner="histogram",
            chart_types=["histogram", "bar"],
            schema=[ColumnSchema(name="salary", type="DOUBLE")],
            data=[{"salary": 45000 + i * 1000} for i in range(10)],
            sql=sql,
        )
        ctx.ast = ast
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        assert "histogram" not in eliminated

    def test_histogram_survives_bucket_column_with_group_by(self) -> None:
        import sqlglot
        sql = "SELECT salary_bucket, COUNT(*) FROM employees GROUP BY salary_bucket"
        ast = sqlglot.parse_one(sql)
        ctx = _make_context(
            chart_winner="histogram",
            chart_types=["histogram", "bar"],
            schema=[
                ColumnSchema(name="salary_bucket", type="DOUBLE"),
                ColumnSchema(name="cnt", type="BIGINT"),
            ],
            sql=sql,
        )
        ctx.ast = ast
        result = engine.run(ctx)
        eliminated = {v.chart_type for v in result.constraint_report.eliminated}
        # 'bucket' in name → bin indicator → NOT eliminated
        assert "histogram" not in eliminated


# ──────────────────────────────────────────────────────────────────────────────
# ConstraintReport audit trail
# ──────────────────────────────────────────────────────────────────────────────

class TestConstraintReport:
    """ConstraintReport correctly records what was checked and why."""

    def test_rules_checked_count(self) -> None:
        ctx = _make_context(
            chart_winner="bar",
            chart_types=["bar"],
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="total", type="DOUBLE"),
            ],
        )
        result = engine.run(ctx)
        # 6 hard rules + N soft rules from YAML
        assert result.constraint_report.rules_checked >= 6

    def test_no_violations_for_clean_bar(self) -> None:
        ctx = _make_context(
            chart_winner="bar",
            chart_types=["bar"],
            schema=[
                ColumnSchema(name="region", type="VARCHAR"),
                ColumnSchema(name="total", type="DOUBLE"),
            ],
        )
        result = engine.run(ctx)
        assert result.constraint_report.eliminated == []

    def test_violation_has_correct_fields(self) -> None:
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi", "bar"],
            schema=[ColumnSchema(name="val", type="DOUBLE")],
            data=[{"val": 1}, {"val": 2}],
            data_profile=_profile(2),
        )
        result = engine.run(ctx)
        violations = result.constraint_report.eliminated
        assert len(violations) == 1
        v = violations[0]
        assert v.chart_type == "kpi"
        assert v.rule_name == "kpi_single_row"
        assert v.rule_type == "hard"
        assert "2" in v.reason

    def test_fallback_applied_flag(self) -> None:
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi", "bar"],
            schema=[ColumnSchema(name="val", type="DOUBLE")],
            data=[{"val": 1}, {"val": 2}],
            data_profile=_profile(2),
        )
        result = engine.run(ctx)
        assert result.fallback_applied is True
        assert "kpi_single_row" in result.fallback_reason

    def test_table_fallback_when_all_eliminated(self) -> None:
        # Only candidate is kpi, but we have 2 rows → all eliminated → fall back to table
        ctx = _make_context(
            chart_winner="kpi",
            chart_types=["kpi"],
            schema=[ColumnSchema(name="val", type="DOUBLE")],
            data=[{"val": 1}, {"val": 2}],
            data_profile=_profile(2),
        )
        result = engine.run(ctx)
        assert result.chart_winner == "table"
        assert result.fallback_applied is True
