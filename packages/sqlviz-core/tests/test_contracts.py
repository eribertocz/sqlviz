"""Tests for DataSourceContract and VizEngineContract (DOC3 Section 6)."""
from typing import Any

from sqlviz_core.contracts import DataSourceContract, VizEngineContract
from sqlviz_core.models import ChartSpec, ColumnSchema, QueryContext, QueryResult, SchemaResult
from typing_extensions import get_protocol_members, is_protocol


class TestDataSourceContract:

    def test_import(self) -> None:
        assert DataSourceContract is not None

    def test_is_protocol(self) -> None:
        assert is_protocol(DataSourceContract)

    def test_required_members(self) -> None:
        members = get_protocol_members(DataSourceContract)
        assert "name" in members
        assert "execute" in members
        assert "schema" in members
        assert "test_connection" in members
        assert "describe" in members

    def test_structural_subtyping(self) -> None:
        """A class satisfying the interface passes runtime type check."""
        class DummySource:
            name: str = "dummy"

            def execute(self, sql: str, context: QueryContext) -> QueryResult:
                return QueryResult(rows=[], columns=[], elapsed_ms=0.0)

            def schema(self, table: str) -> SchemaResult:
                return SchemaResult(table=table, columns=[])

            def test_connection(self) -> bool:
                return True

            def describe(self, sql: str) -> list[ColumnSchema]:
                return []

        source = DummySource()
        assert hasattr(source, "name")
        assert callable(source.execute)
        assert callable(source.schema)
        assert callable(source.test_connection)
        assert callable(source.describe)


class TestVizEngineContract:

    def test_import(self) -> None:
        assert VizEngineContract is not None

    def test_is_protocol(self) -> None:
        assert is_protocol(VizEngineContract)

    def test_required_members(self) -> None:
        members = get_protocol_members(VizEngineContract)
        assert "name" in members
        assert "supported_charts" in members
        assert "build_spec" in members
        assert "supports" in members

    def test_structural_subtyping(self) -> None:
        class DummyEngine:
            name: str = "echarts"
            supported_charts: list[str] = ["line", "bar", "kpi", "table"]

            def build_spec(
                self,
                chart_type: str,
                data: list[dict[str, Any]],
                columns: list[ColumnSchema],
            ) -> ChartSpec:
                return ChartSpec(engine="echarts", chart_type=chart_type)

            def supports(self, chart_type: str) -> bool:
                return chart_type in self.supported_charts

        engine = DummyEngine()
        assert hasattr(engine, "name")
        assert hasattr(engine, "supported_charts")
        assert callable(engine.build_spec)
        assert callable(engine.supports)


class TestModels:

    def test_column_schema_defaults(self) -> None:
        col = ColumnSchema(name="revenue", type="DOUBLE")
        assert col.name == "revenue"
        assert col.type == "DOUBLE"
        assert col.nullable is True

    def test_query_result_row_count(self) -> None:
        result = QueryResult(
            rows=[{"id": 1}, {"id": 2}],
            columns=[ColumnSchema(name="id", type="INTEGER")],
        )
        assert result.row_count == 2

    def test_chart_spec_defaults(self) -> None:
        spec = ChartSpec(engine="echarts", chart_type="line")
        assert spec.engine == "echarts"
        assert spec.chart_type == "line"
        assert spec.options == {}
