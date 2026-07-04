from __future__ import annotations

import sqlglot.expressions as exp

from .ast_helpers import (
    count_group_by_columns,
    has_cte,
    has_group_by,
    has_join,
    has_limit,
    has_order_by,
    has_order_by_desc,
    has_window_function,
    is_single_metric_query,
)

TEMPORAL_PATTERNS = {
    "year", "month", "week", "day", "date", "datetime",
    "timestamp", "hora", "fecha", "periodo", "quarter",
    "mes", "año", "semana", "dia", "time", "dt", "created_at",
    "updated_at", "order_date", "sale_date", "event_date",
}


def _has_temporal_dimension(ast: exp.Expression) -> bool:
    """Detect temporal dimension in GROUP BY columns by name or date function."""
    group = ast.find(exp.Group)
    if not group:
        return False

    # GROUP BY ALL (§16.19): check non-aggregated SELECT columns for temporal names
    if group.args.get("all"):
        select = ast.find(exp.Select)
        if select:
            for expr in select.expressions:
                if isinstance(expr, exp.AggFunc) or expr.find(exp.AggFunc):
                    continue
                col_name = (expr.alias or getattr(expr, "name", "")).lower()
                if col_name in TEMPORAL_PATTERNS:
                    return True
        return False

    for col in group.find_all(exp.Column):
        if col.name.lower() in TEMPORAL_PATTERNS:
            return True

    date_funcs = (
        exp.DateTrunc, exp.Extract, exp.DateDiff,
        exp.DateAdd, exp.TimestampTrunc,
    )
    for func_type in date_funcs:
        if group.find(func_type):
            return True

    return False


def generate_fingerprint(ast: exp.Expression | None) -> str:
    """
    Generate a normalized fingerprint from a SQL AST.

    The fingerprint represents the analytical pattern independent of
    table names, column names, or language.

    Examples:
        SELECT SUM(revenue)
            → "SUM_KPI"
        SELECT month, SUM(rev) FROM t GROUP BY month ORDER BY month
            → "TIME_SUM_GROUP1_ORDER_ASC"
        SELECT cat, COUNT(*) FROM t GROUP BY cat ORDER BY 2 DESC LIMIT 10
            → "COUNT_GROUP1_ORDER_DESC_LIMIT"
        SELECT a, b, c FROM t
            → "UNKNOWN"
    """
    if ast is None:
        return "UNKNOWN"

    patterns: list[str] = []

    # 1. KPI pattern — single aggregation, no dimension, no window
    if is_single_metric_query(ast):
        agg_funcs = list(ast.find_all(exp.AggFunc))
        if agg_funcs:
            agg_name = type(agg_funcs[0]).__name__.upper()
            return f"{agg_name}_KPI"

    # 2. Temporal dimension
    if _has_temporal_dimension(ast):
        patterns.append("TIME")

    # 3. Aggregation functions (sorted for consistency)
    agg_funcs = list(ast.find_all(exp.AggFunc))
    if agg_funcs:
        agg_names = sorted({type(a).__name__.upper() for a in agg_funcs})
        patterns.append("_".join(agg_names))

    # 4. GROUP BY column count
    if has_group_by(ast):
        group_count = count_group_by_columns(ast)
        patterns.append(f"GROUP{group_count}")

    # 5. ORDER BY direction
    if has_order_by(ast):
        if has_order_by_desc(ast):
            patterns.append("ORDER_DESC")
        else:
            patterns.append("ORDER_ASC")

    # 6. LIMIT (ranking signal)
    if has_limit(ast):
        patterns.append("LIMIT")

    # 7. Window functions
    if has_window_function(ast):
        patterns.append("WINDOW")

    # 8. CTE
    if has_cte(ast):
        patterns.append("CTE")

    # 9. JOIN
    if has_join(ast):
        patterns.append("JOIN")

    return "_".join(patterns) if patterns else "UNKNOWN"
