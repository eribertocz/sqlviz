from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SQLProfile:
    """
    What the SQL SAYS — built from the AST before execution.
    Distinct from DataProfile (what the results SHOW, after execution).
    Populated by SQLProfileBuilder in Fase B+.
    """

    has_aggregation: bool = False
    has_group_by: bool = False
    has_order_by: bool = False
    has_limit: bool = False
    has_window_function: bool = False
    has_cte: bool = False
    has_subquery: bool = False
    has_having: bool = False
    has_distinct: bool = False

    group_by_columns: list[str] = field(default_factory=list)
    order_by_columns: list[str] = field(default_factory=list)
    aggregation_functions: list[str] = field(default_factory=list)   # SUM, COUNT, AVG…
    select_columns: list[str] = field(default_factory=list)
    table_names: list[str] = field(default_factory=list)
