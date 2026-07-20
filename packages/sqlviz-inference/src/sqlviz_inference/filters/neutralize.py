"""Neutralize `$variable` filter predicates for the "All" selection.

A parametric panel is written as e.g. ``... WHERE region = $region``. There is
no NULL-guard in the SQL, so an "All" selection (or the very first Run, before
any value is chosen) cannot be expressed by *binding* the variable: ``region =
$region`` bound to ``''`` or ``NULL`` returns zero rows, not every row.

Instead we rewrite the query: for each variable the user left as "All" we
replace the boolean predicate that references it with ``TRUE``, so that
dimension stops filtering while every other (chosen) filter still applies.

    WHERE region = $region AND price >= $min     -- region = All
    ->  WHERE TRUE AND price >= $min

Returns ``None`` when the SQL cannot be parsed, or when an "All" variable is
used somewhere that is not a boolean predicate (a projection, ``LIMIT``, …) and
therefore cannot be safely stripped. The caller then falls back to
inference-only rendering, exactly as before this helper existed.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

# A predicate's boolean context: the node types under which a standalone
# condition sits (WHERE ..., x AND y, NOT x, HAVING ...). The predicate we want
# to neutralize is the child of one of these.
_BOOLEAN_PARENTS = (exp.Where, exp.And, exp.Or, exp.Not, exp.Having)


def _predicate_ancestor(node: exp.Expression) -> exp.Expression | None:
    """Return the boolean predicate that owns ``node``, or None.

    Walks up from a ``$var`` placeholder to the nearest ancestor that sits
    directly inside a boolean context (WHERE / AND / OR / NOT / HAVING). That
    ancestor is the whole comparison (``col = $var``), membership test
    (``col IN ($var)``), range (``col BETWEEN $a AND $b``) or LIKE — the unit we
    replace with TRUE. Returns None if we walk out of every boolean context,
    which means the placeholder is not part of a strippable predicate.
    """
    cur = node
    while cur.parent is not None:
        if isinstance(cur.parent, _BOOLEAN_PARENTS):
            return cur
        cur = cur.parent
    return None


def neutralize_filters(sql: str, all_vars: list[str]) -> str | None:
    """Rewrite ``sql`` so every variable in ``all_vars`` stops filtering.

    Args:
        sql: The panel SQL, still containing ``$variable`` placeholders.
        all_vars: Names (without the ``$``) of the variables set to "All".

    Returns:
        The rewritten SQL with each "All" predicate replaced by ``TRUE``, or
        ``None`` if the SQL cannot be parsed or a variable cannot be stripped.
    """
    if not all_vars:
        return sql
    try:
        tree = sqlglot.parse_one(sql, read="duckdb")
    except Exception:
        return None

    # Dedupe by object identity: a range like `col BETWEEN $a AND $b` reaches
    # the same Between node from both placeholders, and replacing an already
    # detached node twice must be avoided.
    targets: dict[int, exp.Expression] = {}
    wanted = set(all_vars)
    for placeholder in tree.find_all(exp.Placeholder):
        if placeholder.name not in wanted:
            continue
        predicate = _predicate_ancestor(placeholder)
        if predicate is None:
            return None  # used outside a boolean predicate — cannot strip safely
        targets[id(predicate)] = predicate

    for predicate in targets.values():
        predicate.replace(exp.true())

    return tree.sql(dialect="duckdb")
