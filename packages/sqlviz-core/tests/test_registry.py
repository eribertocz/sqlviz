"""Tests for DataSourceRegistry and VizEngineRegistry (DOC3 Section 6)."""
from typing import Any

import pytest
from sqlviz_core.models import ChartSpec, ColumnSchema, QueryContext, QueryResult, SchemaResult
from sqlviz_core.registry import DataSourceRegistry, VizEngineRegistry

# ── Dummy implementations ─────────────────────────────────────────────────────

class DummySource:
    def __init__(self, name: str = "dummy") -> None:
        self.name = name

    def execute(self, sql: str, context: QueryContext) -> QueryResult:
        return QueryResult(rows=[], columns=[], elapsed_ms=0.0)

    def schema(self, table: str) -> SchemaResult:
        return SchemaResult(table=table, columns=[])

    def test_connection(self) -> bool:
        return True

    def describe(self, sql: str) -> list[ColumnSchema]:
        return []


class DummyEngine:
    def __init__(self, name: str = "echarts") -> None:
        self.name = name
        self.supported_charts: list[str] = [
            "line", "bar", "kpi", "table",
            "bar_horizontal", "pie", "scatter", "histogram",
        ]

    def build_spec(
        self,
        chart_type: str,
        data: list[dict[str, Any]],
        columns: list[ColumnSchema],
    ) -> ChartSpec:
        return ChartSpec(engine=self.name, chart_type=chart_type)

    def supports(self, chart_type: str) -> bool:
        return chart_type in self.supported_charts


# ── DataSourceRegistry ────────────────────────────────────────────────────────

class TestDataSourceRegistry:

    def test_register_and_get(self) -> None:
        source = DummySource("duckdb")
        DataSourceRegistry.register(source)
        retrieved = DataSourceRegistry.get("duckdb")
        assert retrieved is source

    def test_get_returns_exact_instance(self) -> None:
        source = DummySource("duckdb")
        DataSourceRegistry.register(source)
        assert DataSourceRegistry.get("duckdb") is source

    def test_get_unknown_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="not registered"):
            DataSourceRegistry.get("nonexistent")

    def test_register_multiple_sources(self) -> None:
        src1 = DummySource("duckdb")
        src2 = DummySource("clickhouse")
        DataSourceRegistry.register(src1)
        DataSourceRegistry.register(src2)
        assert DataSourceRegistry.get("duckdb") is src1
        assert DataSourceRegistry.get("clickhouse") is src2

    def test_all_returns_registered_sources(self) -> None:
        src1 = DummySource("duckdb")
        src2 = DummySource("clickhouse")
        DataSourceRegistry.register(src1)
        DataSourceRegistry.register(src2)
        all_sources = DataSourceRegistry.all()
        assert len(all_sources) == 2
        assert src1 in all_sources
        assert src2 in all_sources

    def test_is_registered(self) -> None:
        DataSourceRegistry.register(DummySource("duckdb"))
        assert DataSourceRegistry.is_registered("duckdb") is True
        assert DataSourceRegistry.is_registered("clickhouse") is False

    def test_register_overwrites_existing_name(self) -> None:
        src1 = DummySource("duckdb")
        src2 = DummySource("duckdb")
        DataSourceRegistry.register(src1)
        DataSourceRegistry.register(src2)
        assert DataSourceRegistry.get("duckdb") is src2

    def test_clear_empties_registry(self) -> None:
        DataSourceRegistry.register(DummySource("duckdb"))
        DataSourceRegistry.clear()
        assert DataSourceRegistry.all() == []
        with pytest.raises(KeyError):
            DataSourceRegistry.get("duckdb")


# ── VizEngineRegistry ─────────────────────────────────────────────────────────

class TestVizEngineRegistry:

    def test_register_and_get(self) -> None:
        engine = DummyEngine("echarts")
        VizEngineRegistry.register(engine)
        retrieved = VizEngineRegistry.get("echarts")
        assert retrieved is engine

    def test_get_unknown_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="not registered"):
            VizEngineRegistry.get("nonexistent")

    def test_get_for_chart_returns_supporting_engine(self) -> None:
        engine = DummyEngine("echarts")
        VizEngineRegistry.register(engine)
        result = VizEngineRegistry.get_for_chart("line")
        assert result is engine

    def test_get_for_chart_raises_when_none_support(self) -> None:
        VizEngineRegistry.register(DummyEngine("echarts"))
        with pytest.raises(KeyError, match="No VizEngine supports"):
            VizEngineRegistry.get_for_chart("unknown_chart_type")

    def test_register_multiple_engines(self) -> None:
        echarts = DummyEngine("echarts")
        plotly = DummyEngine("plotly")
        VizEngineRegistry.register(echarts)
        VizEngineRegistry.register(plotly)
        assert VizEngineRegistry.get("echarts") is echarts
        assert VizEngineRegistry.get("plotly") is plotly

    def test_all_returns_registered_engines(self) -> None:
        engine = DummyEngine("echarts")
        VizEngineRegistry.register(engine)
        assert engine in VizEngineRegistry.all()

    def test_is_registered(self) -> None:
        VizEngineRegistry.register(DummyEngine("echarts"))
        assert VizEngineRegistry.is_registered("echarts") is True
        assert VizEngineRegistry.is_registered("plotly") is False

    def test_clear_empties_registry(self) -> None:
        VizEngineRegistry.register(DummyEngine("echarts"))
        VizEngineRegistry.clear()
        assert VizEngineRegistry.all() == []
