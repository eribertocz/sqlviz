from __future__ import annotations

from dataclasses import dataclass, field

from .column_schema import ColumnSchema


@dataclass
class QueryContext:
    """Execution context passed to DataSourceContract.execute().

    Carries connection identity and prepared-statement parameters.
    Parameters are bound values for $variable substitution — never
    string-interpolated into SQL (DOC7 Section 6.2).
    """

    connection_name: str = "default"
    parameters: list[object] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result of a DataSource query execution."""

    rows: list[dict[str, object]]
    columns: list[ColumnSchema]
    elapsed_ms: float = 0.0

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass
class SchemaResult:
    """Schema description of a table from DataSourceContract.schema()."""

    table: str
    columns: list[ColumnSchema]
