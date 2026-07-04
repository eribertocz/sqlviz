from __future__ import annotations

from typing import Any

from sqlviz_core.models import ColumnSchema

from ..utils.math_utils import (
    compute_trend_direction,
    compute_trend_strength,
    has_statistical_outliers,
)

NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL",
}

# Continuous types preferred over integer types when extracting metric values
# (avoids picking a time/index column before a revenue/metric column).
CONTINUOUS_TYPES = {"FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL"}

DATE_TYPES = {
    "DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE",
    "TIMESTAMP_S", "TIMESTAMP_MS", "TIMESTAMP_NS",
}


def _get_numeric_values(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> list[float]:
    """
    Extract metric column values as floats.
    Prefers DOUBLE/FLOAT/DECIMAL over INTEGER to pick metrics (revenue,
    profit) before dimension indices (month_id, row_number).
    Falls back to any NUMERIC_TYPE if no continuous column is found.
    """
    for pass_types in (CONTINUOUS_TYPES, NUMERIC_TYPES):
        for col in schema:
            if col.type.upper().split("(")[0] in pass_types:
                values: list[float] = []
                for row in data:
                    val = row.get(col.name)
                    if val is not None:
                        try:
                            values.append(float(val))
                        except (TypeError, ValueError):
                            pass
                if values:
                    return values
    return []


def _get_date_values(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> list[str]:
    """Extract first date/timestamp column values as strings."""
    for col in schema:
        if col.type.upper().split("(")[0] in DATE_TYPES:
            return [
                str(row.get(col.name, ""))
                for row in data
                if row.get(col.name) is not None
            ]
    return []


def compute_dim25_row_count(data: list[dict[str, Any]]) -> float:
    """dim 25 — row_count normalized to [0, 1], capped at 10 000."""
    return min(len(data) / 10000.0, 1.0)


def compute_dim26_cardinality(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> float:
    """
    dim 26 — cardinality ratio of the first categorical column.
    unique_values / total_rows → [0, 1].
    """
    if not data:
        return 0.0
    for col in schema:
        col_type = col.type.upper().split("(")[0]
        if col_type not in NUMERIC_TYPES and col_type not in DATE_TYPES:
            values = [row.get(col.name) for row in data if row.get(col.name)]
            if values:
                unique = len(set(str(v) for v in values))
                return unique / len(values)
    return 0.0


def compute_dim27_temporal_cardinality(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> float:
    """
    dim 27 — distinct time periods / 366 → [0, 1].
    """
    date_values = _get_date_values(data, schema)
    if not date_values:
        return 0.0
    return min(len(set(date_values)) / 366.0, 1.0)


def compute_dim28_trend_strength(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> float:
    """dim 28 — R² of linear regression on the metric column."""
    values = _get_numeric_values(data, schema)
    if len(values) < 3:
        return 0.0
    return compute_trend_strength(values)


def compute_dim29_has_outliers(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> float:
    """dim 29 — 1.0 if metric column has Z-score > 3 outliers."""
    values = _get_numeric_values(data, schema)
    if len(values) < 4:
        return 0.0
    return 1.0 if has_statistical_outliers(values) else 0.0


def compute_dim38_trend_direction(
    data: list[dict[str, Any]],
    schema: list[ColumnSchema],
) -> float:
    """
    dim 38 — direction of linear trend, [0.0, 1.0].
    0.0 = declining, 0.5 = flat, 1.0 = growing.
    Kept separate from dim 28 (trend_strength / R²) — see DOC5 §16.2.
    """
    values = _get_numeric_values(data, schema)
    if len(values) < 3:
        return 0.5
    return compute_trend_direction(values)
