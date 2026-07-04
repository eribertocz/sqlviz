from __future__ import annotations

from sqlviz_core.models import ColumnSchema

DATE_TYPES = {
    "DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE",
    "TIMESTAMP_S", "TIMESTAMP_MS", "TIMESTAMP_NS",
    "TIME", "INTERVAL",
}

NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "INT", "BIGINT",
    "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC",
    "REAL", "INT2", "INT4", "INT8",
}

STRING_TYPES = {"VARCHAR", "TEXT", "CHAR", "BPCHAR", "STRING", "BLOB"}

BOOLEAN_TYPES = {"BOOLEAN", "BOOL"}


def compute(schema: list[ColumnSchema]) -> list[float]:
    """
    Compute column type features (dims 18-24).
    Returns 7 floats.
    """
    if not schema:
        return [0.0] * 7

    total = len(schema)
    types = [col.type.upper().split("(")[0] for col in schema]

    has_date = any(t in DATE_TYPES for t in types)
    has_numeric = any(t in NUMERIC_TYPES for t in types)
    has_string = any(t in STRING_TYPES for t in types)

    numeric_count = sum(1 for t in types if t in NUMERIC_TYPES)
    date_count = sum(1 for t in types if t in DATE_TYPES)

    return [
        1.0 if has_date else 0.0,                              # dim 18
        1.0 if has_numeric else 0.0,                           # dim 19
        1.0 if has_string else 0.0,                            # dim 20
        numeric_count / total,                                 # dim 21
        date_count / total,                                    # dim 22
        1.0 if numeric_count == 1 and total <= 2 else 0.0,    # dim 23
        1.0 if numeric_count >= 2 and date_count == 0 else 0.0,  # dim 24
    ]
