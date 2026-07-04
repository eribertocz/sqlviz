"""Filter Engine tests -- DOC5 Section 10.5."""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import FilterControl, RuntimeContext
from sqlviz_inference.filters.filter_engine import FilterEngine
from sqlviz_inference.filters.range_pairing import pair_range_filters
from sqlviz_inference.parser.sql_parser import SQLParser

parser = SQLParser()
filters = FilterEngine()


def detect_filters(
    sql: str,
    schema_defs: list[tuple[str, str]],
) -> list[FilterControl]:
    schema = [ColumnSchema(name=n, type=t) for n, t in schema_defs]
    ctx = RuntimeContext(sql=sql, schema=schema)
    ctx = parser.run(ctx)
    ctx = filters.run(ctx)
    return ctx.filter_controls


class TestBasicDetection:

    def test_dropdown_for_varchar_equality(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM sales WHERE region = $region",
            schema_defs=[("region", "VARCHAR")],
        )
        assert len(controls) == 1
        assert controls[0].control_type == "dropdown"
        assert controls[0].variable == "region"

    def test_date_picker_for_date_equality(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM sales WHERE fecha = $fecha",
            schema_defs=[("fecha", "DATE")],
        )
        assert controls[0].control_type == "date_picker"

    def test_numeric_for_integer(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM sales WHERE quantity = $cantidad",
            schema_defs=[("quantity", "INTEGER")],
        )
        assert controls[0].control_type == "numeric"

    def test_toggle_for_boolean(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM users WHERE active = $activo",
            schema_defs=[("active", "BOOLEAN")],
        )
        assert controls[0].control_type == "toggle"


class TestMultiSelect:

    def test_multiselect_for_any(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM sales WHERE region = ANY($regiones)",
            schema_defs=[("region", "VARCHAR")],
        )
        assert controls[0].control_type == "multiselect"


class TestSearch:

    def test_search_for_ilike(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM products WHERE name ILIKE '%' || $busqueda || '%'",
            schema_defs=[("name", "VARCHAR")],
        )
        assert controls[0].control_type == "search"


class TestMultipleVariables:

    def test_multiple_filters_detected(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM sales WHERE region = $region AND fecha >= $desde",
            schema_defs=[("region", "VARCHAR"), ("fecha", "DATE")],
        )
        assert len(controls) == 2
        variables = {c.variable for c in controls}
        assert variables == {"region", "desde"}


class TestRangePairing:

    def test_date_range_merged(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM sales WHERE fecha >= $desde AND fecha <= $hasta",
            schema_defs=[("fecha", "DATE")],
        )
        merged = pair_range_filters(controls)
        assert len(merged) == 1
        assert merged[0].control_type == "date_range_picker"

    def test_numeric_range_merged(self) -> None:
        controls = detect_filters(
            sql="SELECT * FROM products WHERE price >= $min AND price <= $max",
            schema_defs=[("price", "DOUBLE")],
        )
        merged = pair_range_filters(controls)
        assert len(merged) == 1
        assert merged[0].control_type == "range_slider"


class TestNoFilters:

    def test_no_variables_returns_empty(self) -> None:
        controls = detect_filters(
            sql="SELECT SUM(revenue) FROM sales",
            schema_defs=[("revenue", "DOUBLE")],
        )
        assert controls == []
