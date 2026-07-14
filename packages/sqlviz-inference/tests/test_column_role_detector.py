"""Tests for ColumnRoleDetector — V0.2 Fase B."""
from __future__ import annotations

import pytest
from sqlviz_core.models import ColumnSchema

from sqlviz_inference.roles.column_role_detector import ColumnRoleDetector

detector = ColumnRoleDetector()


def _col(name: str, col_type: str) -> ColumnSchema:
    return ColumnSchema(name=name, type=col_type)


def _role(name: str, col_type: str) -> str:
    return detector._detect(name, col_type)


class TestIDDetection:
    """Columns ending in _id or _key, or named exactly 'id', are IDs."""

    def test_customer_id_integer(self) -> None:
        assert _role("customer_id", "INTEGER") == "id"

    def test_user_key_bigint(self) -> None:
        assert _role("user_key", "BIGINT") == "id"

    def test_exact_id_integer(self) -> None:
        assert _role("id", "INTEGER") == "id"

    def test_order_id_double(self) -> None:
        # Even if type is DOUBLE, _id suffix → id wins over metric
        assert _role("order_id", "DOUBLE") == "id"

    def test_revenue_not_id(self) -> None:
        assert _role("revenue", "DOUBLE") != "id"

    def test_cantidad_not_id(self) -> None:
        assert _role("cantidad", "INTEGER") != "id"

    def test_product_id_varchar(self) -> None:
        assert _role("product_id", "VARCHAR") == "id"


class TestTemporalDetection:
    """Columns with DATE/TIMESTAMP types, or temporal semantic names, get role 'time'."""

    def test_date_type(self) -> None:
        assert _role("fecha", "DATE") == "time"

    def test_timestamp_type(self) -> None:
        assert _role("created_at", "TIMESTAMP") == "time"

    def test_mes_varchar_temporal_name(self) -> None:
        # 'mes' matches TEMPORAL_DIMENSION in semantic dictionary
        assert _role("mes", "VARCHAR") == "time"

    def test_trimestre_varchar(self) -> None:
        assert _role("trimestre", "VARCHAR") == "time"

    def test_anio_varchar(self) -> None:
        assert _role("anio", "VARCHAR") == "time"

    def test_month_varchar(self) -> None:
        assert _role("month", "VARCHAR") == "time"

    def test_semana_varchar(self) -> None:
        assert _role("semana", "VARCHAR") == "time"

    def test_nombre_varchar_not_temporal(self) -> None:
        assert _role("nombre", "VARCHAR") != "time"

    def test_ciudad_varchar_not_temporal(self) -> None:
        assert _role("ciudad", "VARCHAR") != "time"

    def test_integer_year_column_ano(self) -> None:
        # 'ano' exact match → temporal; type is INTEGER but name wins
        assert _role("ano", "INTEGER") == "time"


class TestRankDetection:
    """Rank columns detected by name."""

    def test_rank_integer(self) -> None:
        assert _role("rank", "INTEGER") == "rank"

    def test_rn_bigint(self) -> None:
        assert _role("rn", "BIGINT") == "rank"

    def test_position_integer(self) -> None:
        assert _role("position", "INTEGER") == "rank"

    def test_row_number_bigint(self) -> None:
        assert _role("row_number", "BIGINT") == "rank"

    def test_revenue_not_rank(self) -> None:
        assert _role("revenue", "DOUBLE") != "rank"

    def test_total_not_rank(self) -> None:
        assert _role("total", "BIGINT") != "rank"


class TestPercentageDetection:
    """Percentage/ratio columns detected by name."""

    def test_pct_double(self) -> None:
        assert _role("pct", "DOUBLE") == "percentage"

    def test_tasa_double(self) -> None:
        assert _role("tasa", "DOUBLE") == "percentage"

    def test_margin_pct_double(self) -> None:
        assert _role("margin_pct", "DOUBLE") == "percentage"

    def test_conversion_rate_double(self) -> None:
        assert _role("conversion_rate", "DOUBLE") == "percentage"

    def test_cuota_double(self) -> None:
        assert _role("cuota", "DOUBLE") == "percentage"

    def test_revenue_not_percentage(self) -> None:
        assert _role("revenue", "DOUBLE") != "percentage"

    def test_count_not_percentage(self) -> None:
        assert _role("count", "BIGINT") != "percentage"


class TestMetricDetection:
    """Numeric non-id, non-rank, non-percentage columns → 'metric'."""

    def test_revenue_double(self) -> None:
        assert _role("revenue", "DOUBLE") == "metric"

    def test_total_bigint(self) -> None:
        assert _role("total", "BIGINT") == "metric"

    def test_cantidad_integer(self) -> None:
        assert _role("cantidad", "INTEGER") == "metric"

    def test_ingresos_numeric(self) -> None:
        assert _role("ingresos", "NUMERIC") == "metric"

    def test_varchar_not_metric(self) -> None:
        assert _role("nombre", "VARCHAR") != "metric"


class TestDimensionAndCategory:
    """Non-numeric non-temporal non-entity columns → 'dimension' or 'category'."""

    def test_nombre_dimension(self) -> None:
        assert _role("nombre", "VARCHAR") == "dimension"

    def test_email_dimension(self) -> None:
        assert _role("email", "VARCHAR") == "dimension"

    def test_canal_venta_dimension(self) -> None:
        assert _role("canal_venta", "VARCHAR") == "dimension"

    def test_region_category(self) -> None:
        # 'region' matches GEOGRAPHIC_DIMENSION → category
        assert _role("region", "VARCHAR") == "category"

    def test_city_category(self) -> None:
        # 'city' matches GEOGRAPHIC_DIMENSION → category
        assert _role("city", "VARCHAR") == "category"


class TestBuildMethod:
    """Full schema → ColumnRoles integration."""

    def test_mixed_schema(self) -> None:
        schema = [
            _col("customer_id", "INTEGER"),
            _col("mes", "VARCHAR"),
            _col("revenue", "DOUBLE"),
            _col("canal_venta", "VARCHAR"),
        ]
        roles = detector.build(schema)
        role_map = {r.name: r.role for r in roles.roles}
        assert role_map["customer_id"] == "id"
        assert role_map["mes"] == "time"
        assert role_map["revenue"] == "metric"
        assert role_map["canal_venta"] == "dimension"

    def test_kpi_schema_single_numeric(self) -> None:
        schema = [_col("total_revenue", "DOUBLE")]
        roles = detector.build(schema)
        assert roles.roles[0].role == "metric"

    def test_all_roles_valid(self) -> None:
        from sqlviz_inference.contracts.column_roles import VALID_ROLES
        schema = [
            _col("id", "INTEGER"),
            _col("mes", "VARCHAR"),
            _col("rank", "INTEGER"),
            _col("tasa", "DOUBLE"),
            _col("revenue", "DOUBLE"),
            _col("nombre", "VARCHAR"),
        ]
        roles = detector.build(schema)
        for r in roles.roles:
            assert r.role in VALID_ROLES, f"{r.name} got invalid role {r.role!r}"
