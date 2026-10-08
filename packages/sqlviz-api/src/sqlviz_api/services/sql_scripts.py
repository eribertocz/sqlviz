"""DuckDB syntax extraction only: never bind or execute an author's SQL."""

from __future__ import annotations

from threading import BoundedSemaphore

import duckdb
from sqlviz_core.models.sql_script import (
    MAX_SQL_SCRIPT_STATEMENTS,
    SqlScriptError,
    SqlStatement,
    validate_sql_script,
)

from sqlviz_api.services.queries import QueryFailure


def _utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


class SqlScriptService:
    """App-local admission; each parse owns and closes an empty native catalog."""

    def __init__(self) -> None:
        self._slots = BoundedSemaphore(2)

    def parse(self, sql: str) -> tuple[SqlStatement, ...]:
        validate_sql_script(sql)
        if not self._slots.acquire(blocking=False):
            raise QueryFailure(429, "sql_parse_busy", "SQL analysis is busy; retry shortly")
        try:
            connection = duckdb.connect(":memory:", config={
                "enable_external_access": False,
                "autoload_known_extensions": False,
                "autoinstall_known_extensions": False,
                "threads": 1,
                "memory_limit": "64MB",
            })
            try:
                native = connection.extract_statements(sql)
            except (duckdb.ParserException, RecursionError):
                raise SqlScriptError(
                    "sql_script_invalid",
                    "SQL syntax is invalid. Check strings, comments and statement boundaries.",
                ) from None
            finally:
                connection.close()
        finally:
            self._slots.release()
        if len(native) > MAX_SQL_SCRIPT_STATEMENTS:
            raise SqlScriptError("sql_script_limit", "SQL script exceeds 256 statements")

        statements: list[SqlStatement] = []
        cursor = 0
        for statement in native:
            # DuckDB supplies original source, including comments. Never
            # regenerate SQL from an AST or discover boundaries by semicolons.
            raw: str = statement.query
            start = sql.find(raw, cursor)
            if start < 0 or not raw.strip():
                raise SqlScriptError("sql_script_invalid", "SQL source positions could not be read")
            cursor = start + len(raw)
            end = cursor - (len(raw) - len(raw.rstrip()))
            start += len(raw) - len(raw.lstrip())
            statements.append(SqlStatement(
                sql[start:end], _utf16_length(sql[:start]), _utf16_length(sql[:end]),
            ))
        return tuple(statements)
