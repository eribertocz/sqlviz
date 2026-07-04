from __future__ import annotations

import sqlglot
import sqlglot.expressions as exp


def parse_sql(sql: str, dialect: str = "duckdb") -> exp.Expression | None:
    """Parse SQL string to AST. Returns None if invalid — never raises."""
    try:
        return sqlglot.parse_one(sql, dialect=dialect)  # type: ignore[return-value]
    except Exception:
        return None


def has_group_by(ast: exp.Expression) -> bool:
    return ast.find(exp.Group) is not None


def has_order_by(ast: exp.Expression) -> bool:
    return ast.find(exp.Order) is not None


def has_order_by_desc(ast: exp.Expression) -> bool:
    order = ast.find(exp.Order)
    if not order:
        return False
    directions = list(order.find_all(exp.Ordered))
    return any(d.args.get("desc") for d in directions)


def has_limit(ast: exp.Expression) -> bool:
    return ast.find(exp.Limit) is not None


def has_aggregation(ast: exp.Expression) -> bool:
    return bool(list(ast.find_all(exp.AggFunc)))


def has_sum(ast: exp.Expression) -> bool:
    return ast.find(exp.Sum) is not None


def has_count(ast: exp.Expression) -> bool:
    return ast.find(exp.Count) is not None


def has_avg(ast: exp.Expression) -> bool:
    return ast.find(exp.Avg) is not None


def has_window_function(ast: exp.Expression) -> bool:
    return ast.find(exp.Window) is not None


def has_cte(ast: exp.Expression) -> bool:
    return ast.find(exp.With) is not None


def has_join(ast: exp.Expression) -> bool:
    return ast.find(exp.Join) is not None


def has_where(ast: exp.Expression) -> bool:
    return ast.find(exp.Where) is not None


def has_subquery(ast: exp.Expression) -> bool:
    selects = list(ast.find_all(exp.Select))
    return len(selects) > 1


def has_partition_by(ast: exp.Expression) -> bool:
    window = ast.find(exp.Window)
    if not window:
        return False
    return window.find(exp.PartitionedByProperty) is not None


def has_case_when(ast: exp.Expression) -> bool:
    return ast.find(exp.Case) is not None


def has_distinct(ast: exp.Expression) -> bool:
    return ast.find(exp.Distinct) is not None


def count_group_by_columns(ast: exp.Expression) -> int:
    """Count grouping keys in the GROUP BY clause.

    Three syntactic forms (§16.19, §16.27):
      GROUP BY a, b   — named columns     → count group.expressions directly
      GROUP BY 1, 2   — positional ints   → count group.expressions directly (§16.27)
      GROUP BY ALL    — synthetic form    → count non-aggregated SELECT columns
    """
    group = ast.find(exp.Group)
    if not group:
        return 0
    # GROUP BY ALL (§16.19): synthetic — infer count from SELECT
    if group.args.get("all"):
        select = ast.find(exp.Select)
        if not select:
            return 0
        return sum(
            1 for expr in select.expressions
            if not (isinstance(expr, exp.AggFunc) or expr.find(exp.AggFunc))
        )
    # Named (GROUP BY a, b) and positional (GROUP BY 1, 2):
    # each item in group.expressions is exactly one grouping key.
    return len(group.expressions)


def count_select_columns(ast: exp.Expression) -> int:
    select = ast.find(exp.Select)
    if not select:
        return 0
    return len(list(select.find_all(exp.Column)))


def get_table_names(ast: exp.Expression) -> list[str]:
    tables = ast.find_all(exp.Table)
    return [t.name.lower() for t in tables if t.name]


def get_column_names_from_select(ast: exp.Expression) -> list[str]:
    select = ast.find(exp.Select)
    if not select:
        return []
    names = []
    for expr in select.expressions:
        alias = getattr(expr, "alias", "")
        name = getattr(expr, "name", "")
        if alias:
            names.append(str(alias).lower())
        elif name:
            names.append(str(name).lower())
    return names


def is_single_metric_query(ast: exp.Expression) -> bool:
    """
    True if the query produces exactly one aggregated metric with no GROUP BY
    and no window function. Strongest KPI signal.
    Example: SELECT SUM(revenue) FROM sales
    """
    return (
        has_aggregation(ast)
        and not has_group_by(ast)
        and not has_window_function(ast)
        and count_select_columns(ast) <= 2
    )


def has_qualify(ast: exp.Expression) -> bool:
    """True when a QUALIFY clause is present (DuckDB window-filter syntax, §16.32)."""
    return ast.find(exp.Qualify) is not None


def has_percentile(ast: exp.Expression) -> bool:
    """True when the query uses percentile/quantile aggregate functions (§16.33).
    Covers quantile_cont → PercentileCont and quantile_disc → PercentileDisc."""
    return (
        ast.find(exp.PercentileCont) is not None
        or ast.find(exp.PercentileDisc) is not None
    )


def is_ranking_pattern(ast: exp.Expression) -> bool:
    """True for ORDER BY DESC + LIMIT N (explicit ranking pattern)."""
    return has_order_by_desc(ast) and has_limit(ast)


def has_part_of_whole_pattern(ast: exp.Expression) -> bool:
    """
    Detect the DOC4 §19.4 share formula: x / AGG(x) OVER ().
    The denominator must be a window over a TOTAL aggregate (SUM/AVG/COUNT/
    MAX/MIN) with no PARTITION BY (i.e., sums across ALL rows).

    Deliberately excludes LAG/LEAD and other analytical functions so that
    growth-rate expressions like SUM(x) / LAG(SUM(x)) OVER (ORDER BY t)
    do not trigger false positives (§16.21).

    Catches:
      SUM(monto)  / SUM(SUM(monto)) OVER ()    — standard share formula
      monto       / SUM(monto)      OVER ()    — row-level share
    """
    if ast is None:
        return False
    # Only these aggregates represent a "total" in the denominator.
    _TOTAL_AGGS = (exp.Sum, exp.Avg, exp.Count, exp.Max, exp.Min)
    for div in ast.find_all(exp.Div):
        right = div.args.get("expression")
        if isinstance(right, exp.Window) and isinstance(right.this, _TOTAL_AGGS):
            if right.find(exp.PartitionedByProperty) is None:
                return True
    return False
