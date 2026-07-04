from __future__ import annotations

from typing import Protocol

from sqlviz_core.models import ColumnSchema, QueryContext, QueryResult, SchemaResult


class DataSourceContract(Protocol):
    """Contract that every data source must satisfy.

    Implementations registered in DataSourceRegistry.
    V0.1: DuckDB only. V0.2+: ClickHouse, etc. (DOC3 Section 5).
    Adding a new source never requires changing this contract.
    """

    name: str

    def execute(self, sql: str, context: QueryContext) -> QueryResult: ...

    def schema(self, table: str) -> SchemaResult: ...

    def test_connection(self) -> bool: ...

    def describe(self, sql: str) -> list[ColumnSchema]: ...
