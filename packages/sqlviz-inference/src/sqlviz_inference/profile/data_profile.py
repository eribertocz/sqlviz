from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from sqlviz_core.models import ColumnSchema

from ..utils.sqlviz_logging import get_logger

_log = get_logger("data_profile")

if TYPE_CHECKING:
    from ..context import RuntimeContext

_NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
}


@dataclass
class ColumnProfile:
    name: str
    type: str
    cardinality: int       # distinct non-null value count
    null_count: int
    null_fraction: float   # null_count / row_count
    max_label_length: int  # max len(str(value)) across non-null values
    mean_label_length: float
    is_numeric: bool


@dataclass
class DataProfile:
    row_count: int
    col_count: int
    single_row: bool                                   # row_count == 1
    wide_table: bool                                   # row_count > 20 and col_count > 5
    column_profiles: list[ColumnProfile] = field(default_factory=list)


class ResultProfiler:
    """
    Builds a DataProfile from actual query results.
    Runs after SQL execution — captures what the data SHOWS,
    not what the SQL says (that's SQLProfile, Fase A).
    """

    def build(
        self,
        data: list[dict[str, Any]],
        schema: list[ColumnSchema],
    ) -> DataProfile:
        row_count = len(data)

        if schema:
            col_specs = [(c.name, c.type.upper().split("(")[0]) for c in schema]
        elif data:
            col_specs = [(k, "UNKNOWN") for k in data[0].keys()]
        else:
            col_specs = []

        col_count = len(col_specs)

        column_profiles: list[ColumnProfile] = []
        for col_name, col_type in col_specs:
            values = [row.get(col_name) for row in data]
            non_null = [v for v in values if v is not None]
            null_count = row_count - len(non_null)
            null_fraction = null_count / row_count if row_count > 0 else 0.0

            str_vals = [str(v) for v in non_null]
            cardinality = len(set(str_vals))

            if str_vals:
                lengths = [len(s) for s in str_vals]
                max_label_length = max(lengths)
                mean_label_length = sum(lengths) / len(lengths)
            else:
                max_label_length = 0
                mean_label_length = 0.0

            column_profiles.append(ColumnProfile(
                name=col_name,
                type=col_type,
                cardinality=cardinality,
                null_count=null_count,
                null_fraction=null_fraction,
                max_label_length=max_label_length,
                mean_label_length=mean_label_length,
                is_numeric=col_type in _NUMERIC_TYPES,
            ))

        return DataProfile(
            row_count=row_count,
            col_count=col_count,
            single_row=row_count == 1,
            wide_table=row_count > 20 and col_count > 5,
            column_profiles=column_profiles,
        )

    def run(self, context: RuntimeContext) -> RuntimeContext:
        try:
            context.data_profile = self.build(context.data, context.schema)
        except Exception as e:
            _log.warning("%s", e, extra={"trace_id": context.trace_id})
            context = context.with_error("ResultProfiler", str(e))
        return context
