from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ColumnSchema:
    """Schema of a single column from DuckDB DESCRIBE.

    Canonical definition — imported by sqlviz-inference (context.py)
    and sqlviz-storage (schema.py). Never duplicated.
    DOC8 Phase 1 correction: moved here from sqlviz-inference/context.py.
    """

    name: str
    type: str  # DuckDB type string: "VARCHAR" | "DOUBLE" | "DATE" | ...
    nullable: bool = True
