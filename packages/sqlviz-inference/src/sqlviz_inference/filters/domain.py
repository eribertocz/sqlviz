"""Build a *domain query* for a filter column.

Given the panel SQL that contains a `$variable` filtering `column`, we want
the set of values the UI control should offer:

  - ``distinct`` — the distinct values of ``column`` (for dropdown / multiselect
    / checkbox controls), sorted, NULLs dropped, capped.
  - ``range``    — the ``MIN`` / ``MAX`` of ``column`` (for a slider's bounds).

The panel SQL still contains the ``$variable`` placeholders, so we cannot run
it directly to learn the column's domain (binding the vars to anything either
filters the result or errors). Instead we rewrite the query with sqlglot:
strip the ``WHERE`` / ``GROUP BY`` / ``ORDER BY`` / ``HAVING`` / ``LIMIT`` (all
of which may reference the variable or collapse the rows) and project just the
target column from the remaining ``FROM`` / ``JOIN`` sources. That gives the
full domain of the column independent of the current filter selection.

Returns ``None`` when the SQL cannot be parsed or the column projected — the
caller then falls back to a plain text/number input, so a control is never
worse than before this enrichment existed.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

_DISTINCT_LIMIT = 200


def build_domain_query(sql: str, column: str, kind: str) -> str | None:
    """Return a DuckDB SQL string that yields ``column``'s domain, or None.

    ``kind`` is ``"distinct"`` (one column of values) or ``"range"`` (a single
    row of ``lo, hi``).
    """
    try:
        tree = sqlglot.parse_one(sql, read="duckdb")
    except Exception:
        return None

    select = tree if isinstance(tree, exp.Select) else tree.find(exp.Select)
    if select is None:
        return None

    # Keep only the row-producing part (FROM + JOINs); drop every clause that
    # could reference the $variable or collapse/limit the rows.
    src = select.copy()
    if src.find(exp.From) is None:
        return None
    for clause in ("where", "group", "order", "having", "qualify", "limit", "distinct"):
        src.set(clause, None)

    col = exp.column(column)
    try:
        if kind == "distinct":
            inner = src.select(col, append=False).distinct()
            query: exp.Expression = (
                exp.select(exp.column(column))
                .from_(inner.subquery("d"))
                .where(exp.column(column).is_(exp.null()).not_())
                .order_by(exp.column(column))
                .limit(_DISTINCT_LIMIT)
            )
        elif kind == "range":
            inner = src.select(col, append=False)
            query = exp.select(
                exp.func("MIN", exp.column(column)).as_("lo"),
                exp.func("MAX", exp.column(column)).as_("hi"),
            ).from_(inner.subquery("d"))
        else:
            return None
        return query.sql(dialect="duckdb")
    except Exception:
        return None
