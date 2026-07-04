"""JSON serialization helpers for DuckDB query results.

DuckDB returns Python types that json.dumps cannot handle directly.
json_safe() converts every value to a JSON-serializable primitive,
recursing into lists and dicts (ARRAY, LIST, STRUCT, MAP columns).

Call it on every cell value before building the response payload:
    {k: json_safe(v) for k, v in zip(col_names, row)}
"""

from __future__ import annotations

import datetime
import math
import uuid
from decimal import Decimal


def json_safe(val: object) -> object:
    """Return a JSON-serializable equivalent of *val*.

    Conversion table
    ----------------
    Python type          JSON output
    ────────────────     ───────────────────────────────────────────
    None                 null
    bool                 true / false  (checked before int)
    int                  number
    float (finite)       number
    float NaN/Infinity   null          (JSON has no NaN/Inf)
    Decimal (finite)     number (float)
    Decimal NaN/Infinity null
    str                  string
    datetime.datetime    ISO-8601 string  "2024-01-15T10:30:00"
    datetime.date        ISO-8601 string  "2024-01-15"
    datetime.time        ISO-8601 string  "10:30:00"
    datetime.timedelta   total seconds as float
    uuid.UUID            string  "550e8400-…"
    bytes (BLOB)         hex string  "deadbeef"
    list / tuple         array   (elements recursed)
    dict                 object  (keys str-coerced, values recursed)
    anything else        str(val)  (safe fallback, never raises)
    """
    # ── None ──────────────────────────────────────────────────────────────────
    if val is None:
        return None

    # ── bool before int (bool is a subclass of int) ──────────────────────────
    if isinstance(val, bool):
        return val

    # ── Integers ──────────────────────────────────────────────────────────────
    if isinstance(val, int):
        return val

    # ── Floats — guard against NaN / ±Infinity which are invalid JSON ─────────
    if isinstance(val, float):
        return None if (math.isnan(val) or math.isinf(val)) else val

    # ── Decimal (DECIMAL / NUMERIC columns) ───────────────────────────────────
    if isinstance(val, Decimal):
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f

    # ── Strings ───────────────────────────────────────────────────────────────
    if isinstance(val, str):
        return val

    # ── Temporal — datetime before date (datetime is a subclass of date) ──────
    if isinstance(val, datetime.datetime):
        return val.isoformat()

    if isinstance(val, datetime.date):
        return val.isoformat()

    if isinstance(val, datetime.time):
        return val.isoformat()

    if isinstance(val, datetime.timedelta):
        return val.total_seconds()

    # ── UUID ──────────────────────────────────────────────────────────────────
    if isinstance(val, uuid.UUID):
        return str(val)

    # ── Binary (BLOB) → lowercase hex string ──────────────────────────────────
    if isinstance(val, (bytes, bytearray)):
        return val.hex()

    # ── Compound types — recurse so nested values are also safe ───────────────
    if isinstance(val, (list, tuple)):
        return [json_safe(v) for v in val]

    if isinstance(val, dict):
        return {str(k): json_safe(v) for k, v in val.items()}

    # ── Fallback — covers any DuckDB-specific type not listed above ───────────
    return str(val)
