"""Read-statement eligibility for analytical SQL; not a database sandbox."""

from __future__ import annotations

import sqlglot

from sqlviz_api.services.access import AccessDenied


def validate_read_query(sql: str) -> sqlglot.exp.Query:
    statements = [
        item
        for item in sqlglot.parse(sql, read="duckdb")
        if item is not None and not isinstance(item, sqlglot.exp.Semicolon)
    ]
    if len(statements) != 1 or not isinstance(statements[0], sqlglot.exp.Query):
        raise AccessDenied(403, "Analytical SQL must be a single read query")
    if any(
        isinstance(node, (sqlglot.exp.DDL, sqlglot.exp.DML, sqlglot.exp.Into))
        for node in statements[0].walk()
    ):
        raise AccessDenied(403, "Analytical SQL must be a single read query")
    return statements[0]


def validate_viewer_query(sql: str) -> None:
    try:
        validate_read_query(sql)
    except (sqlglot.errors.ParseError, RecursionError):
        raise AccessDenied(403, "Viewer queries must be a single read query") from None
