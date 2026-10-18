"""Named placeholders from parsed SQL, excluding literals and comments."""

from __future__ import annotations

import sqlglot
from sqlglot import exp


def parameter_names(tree: exp.Query) -> list[str]:
    return list(dict.fromkeys(node.name.lower() for node in tree.find_all(exp.Placeholder)))


def filter_parameter_names(sql: str) -> list[str]:
    try:
        tree = sqlglot.parse_one(sql, read="duckdb")
    except (sqlglot.errors.ParseError, RecursionError):
        return []
    if not isinstance(tree, exp.Query):
        return []
    return parameter_names(tree)
